"""Phase 1b 実 acquisition adapters(docs/phase-1b-acquisition-boundary.md §6)。stdlib のみ(urllib)。

adapter が **transport_status**(通信の成否)と **content_status**(取れた中身が観測に足るか, AB-2)を付す。
AB-2 の肝: HTTP 200 でも Cloudflare challenge / JS-required / auth wall / empty はあり得る → adapter が
body を classify する。adapter honesty(誤分類/嘘)は宣言済み非保証(contracts): 単一プロセスでは検出不能。
"""
import json, socket, base64, urllib.request, urllib.error
from urllib.parse import urlparse

ADAPTER_VERSION = "0.1"
USER_AGENT = "EGL-acquisition/0.1 (research; stdlib urllib)"
TIMEOUT = 20
MAX_BYTES = 5_000_000

# ---- content classification (AB-2): 200 でも中身が観測に足るか ----
_CHALLENGE = [b"cf-browser-verification", b"Just a moment", b"Checking your browser",
              b"cf_chl_", b"_cf_chl_opt", b"challenge-platform", b"Enable JavaScript and cookies to continue"]
_JS_REQ = [b"Please enable JavaScript", b"enable JavaScript to run", b"You need to enable JavaScript"]
_AUTH = [b"Sign in to", b"Please log in", b"Log in to continue", b"authentication required"]


def classify_content(body, content_type, status, headers):
    """transport SUCCESS の body を分類。誤りは adapter honesty 非保証の範囲。"""
    if not body or not body.strip():
        return "EMPTY"
    head = body[:30000]
    server = (headers.get("Server") or "").lower()
    if any(m in head for m in _CHALLENGE) or ("cloudflare" in server and status in (403, 503)):
        return "CHALLENGE_PAGE"
    if any(m in head for m in _AUTH):
        return "AUTH_WALL"
    if any(m in head for m in _JS_REQ) and len(body) < 4000:
        return "PLACEHOLDER"          # JS-required の near-empty shell
    return "OBSERVED"


def _http_get(url, extra_headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(extra_headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read(MAX_BYTES + 1)
            return {"status": resp.status, "headers": dict(resp.headers), "body": body[:MAX_BYTES],
                    "final_url": resp.geturl(), "truncated": len(body) > MAX_BYTES, "error": None}
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read(MAX_BYTES)
        except Exception:
            pass
        return {"status": e.code, "headers": dict(e.headers or {}), "body": body,
                "final_url": url, "truncated": False, "error": "http"}
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
        reason = getattr(e, "reason", e)
        is_to = isinstance(e, (socket.timeout, TimeoutError)) or "timed out" in str(reason).lower()
        return {"status": None, "headers": {}, "body": b"", "final_url": url,
                "truncated": False, "error": "timeout" if is_to else "network"}


def _transport_from(resp):
    if resp["error"] == "timeout":
        return "TIMEOUT"
    if resp["error"] == "network":
        return "NETWORK_ERROR"
    s = resp["status"]
    return {200: "SUCCESS", 401: "AUTH_REQUIRED", 403: "ACCESS_DENIED",
            404: "NOT_FOUND_REMOTE", 410: "NOT_FOUND_REMOTE", 429: "RATE_LIMITED"}.get(
        s, "NOT_RETRIEVABLE")


# ---------- ACQ_HTTP_STATIC ----------
def fetch_http_static(leg):
    url = leg["target_locator"]
    if urlparse(url).scheme not in ("http", "https"):
        return _res("UNSUPPORTED_CONTENT", None, None, None, None, {"reason": "non-http scheme"})
    r = _http_get(url)
    ts = _transport_from(r)
    ctype = r["headers"].get("Content-Type")
    cs = classify_content(r["body"], ctype, r["status"], r["headers"]) if ts == "SUCCESS" else None
    return _res(ts, cs, r["status"], ctype, r["body"] if ts == "SUCCESS" else None,
                {"final_url": r["final_url"], "server": r["headers"].get("Server"), "truncated": r["truncated"]})


# ---------- ACQ_GITHUB(provenance: owner/repo/ref/path/sha)----------
def _parse_github(url):
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) >= 5 and parts[2] in ("blob", "tree"):
        return parts[0], parts[1], parts[3], "/".join(parts[4:])   # owner, repo, ref, path
    if len(parts) >= 2:
        return parts[0], parts[1], None, ""
    return None


def fetch_github(leg):
    g = _parse_github(leg["target_locator"])
    if not g:
        return _res("UNSUPPORTED_CONTENT", None, None, None, None, {"reason": "not a github url"})
    owner, repo, ref, path = g
    api = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}" + (f"?ref={ref}" if ref else "")
    r = _http_get(api, {"Accept": "application/vnd.github+json"})
    ts = _transport_from(r)
    if r["status"] == 403 and b"rate limit" in r["body"].lower():
        ts = "RATE_LIMITED"
    prov = {"owner": owner, "repo": repo, "ref": ref, "path": path}
    cs, raw = None, None
    if ts == "SUCCESS":
        try:
            j = json.loads(r["body"])
            if isinstance(j, dict) and j.get("encoding") == "base64" and "content" in j:
                raw = base64.b64decode(j["content"])
                prov["sha"] = j.get("sha"); prov["html_url"] = j.get("html_url")
                cs = classify_content(raw, "text", 200, r["headers"])
            else:
                raw, cs = r["body"], "UNEXPECTED_CONTENT"   # directory listing / 想定外 payload
        except Exception:
            raw, cs = r["body"], "UNEXPECTED_CONTENT"
    return _res(ts, cs, r["status"], "application/vnd.github+json", raw, prov)


def _res(transport, content, http_status, content_type, raw, prov):
    return {"transport_status": transport, "content_status": content, "http_status": http_status,
            "content_type": content_type, "raw_bytes": raw, "adapter_version": ADAPTER_VERSION,
            "adapter_provenance": prov}


# ---------- ACQ_GITHUB_SEARCH(GitHub issue/PR search API; real fetch of the result set)----------
def fetch_github_search(leg):
    """Real GitHub issue-search acquisition. leg.target_locator = an api.github.com/search/issues URL.
    Returns ONE adapter_result whose provenance carries the parsed result items (html_url/title/body/owner
    /number/state). transport/content status set by the adapter (AB-2). No injected content."""
    url = leg["target_locator"]
    if urlparse(url).scheme not in ("http", "https"):
        return _res("UNSUPPORTED_CONTENT", None, None, None, None, {"reason": "non-http scheme"})
    r = _http_get(url, {"Accept": "application/vnd.github+json"})
    ts = _transport_from(r)
    if r["status"] == 403 and b"rate limit" in r["body"].lower():
        ts = "RATE_LIMITED"
    items, cs = [], None
    if ts == "SUCCESS":
        try:
            j = json.loads(r["body"])
            for it in (j.get("items") or []):
                repo_url = it.get("repository_url") or ""
                owner = repo_url.rsplit("/", 2)[-2] if "/" in repo_url else ""
                items.append({"html_url": it.get("html_url"), "title": it.get("title") or "",
                              "body": (it.get("body") or "")[:4000], "owner": owner,
                              "number": it.get("number"), "state": it.get("state")})
            cs = "OBSERVED" if items else "EMPTY"
        except Exception:
            cs = "UNEXPECTED_CONTENT"
    q = " ".join(leg.get("query") or [])
    return _res(ts, cs, r["status"], "application/vnd.github+json", r["body"] if ts == "SUCCESS" else None,
                {"query": q, "result_count": len(items), "items": items, "search_url": url})


# ---------- ACQ_GITHUB_ISSUE(ITEM-2DER-EVO-0005: dedicated per-issue/PR fetch — real fetch of ONE issue)----------
def fetch_github_issue(leg):
    """Real fetch of a single GitHub issue/PR body (closes the DE-0182 injected-bytes boundary). leg.target_
    locator = a github.com/owner/repo/issues/N (or /pull/N) URL. Returns the issue title+body as raw content."""
    parts = urlparse(leg["target_locator"]).path.strip("/").split("/")
    if len(parts) < 4 or parts[2] not in ("issues", "pull"):
        return _res("UNSUPPORTED_CONTENT", None, None, None, None, {"reason": "not a github issue/pr url"})
    owner, repo, num = parts[0], parts[1], parts[3]
    api = f"https://api.github.com/repos/{owner}/{repo}/issues/{num}"
    r = _http_get(api, {"Accept": "application/vnd.github+json"})
    ts = _transport_from(r)
    if r["status"] == 403 and b"rate limit" in r["body"].lower():
        ts = "RATE_LIMITED"
    prov = {"owner": owner, "repo": repo, "number": num, "issue_url": leg["target_locator"]}
    cs, raw = None, None
    if ts == "SUCCESS":
        try:
            j = json.loads(r["body"])
            title, body = j.get("title") or "", (j.get("body") or "")[:8000]
            raw = (title + "\n\n" + body).encode("utf-8")
            prov.update({"state": j.get("state"), "title": title[:120]})
            cs = "OBSERVED" if body.strip() else "EMPTY"
        except Exception:
            raw, cs = r["body"], "UNEXPECTED_CONTENT"
    return _res(ts, cs, r["status"], "application/vnd.github+json", raw if ts == "SUCCESS" else None, prov)


# ---------- ACQ_GITHUB_PROV(ITEM-2DER-EVO-0006: PR/commit/release provenance — owner/repo/sha/author/date)----------
def fetch_github_prov(leg):
    """Fetch GitHub PR / commit / release PROVENANCE. leg.target_locator = a github.com URL of the form
    .../commit(s)/SHA, .../pull/N, or .../releases/tag/TAG. Returns a provenance summary + structured provenance."""
    parts = urlparse(leg["target_locator"]).path.strip("/").split("/")
    if len(parts) < 4:
        return _res("UNSUPPORTED_CONTENT", None, None, None, None, {"reason": "not a github provenance url"})
    owner, repo, kind = parts[0], parts[1], parts[2]
    if kind in ("commit", "commits"):
        api, ptype = f"https://api.github.com/repos/{owner}/{repo}/commits/{parts[3]}", "commit"
    elif kind == "pull":
        api, ptype = f"https://api.github.com/repos/{owner}/{repo}/pulls/{parts[3]}", "pull"
    elif kind == "releases" and len(parts) >= 5 and parts[3] in ("tag", "tags"):
        api, ptype = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{parts[4]}", "release"
    else:
        return _res("UNSUPPORTED_CONTENT", None, None, None, None, {"reason": "unsupported provenance url"})
    r = _http_get(api, {"Accept": "application/vnd.github+json"})
    ts = _transport_from(r)
    if r["status"] == 403 and b"rate limit" in r["body"].lower():
        ts = "RATE_LIMITED"
    prov = {"kind": ptype, "owner": owner, "repo": repo, "url": leg["target_locator"]}
    cs, raw = None, None
    if ts == "SUCCESS":
        try:
            j = json.loads(r["body"])
            if ptype == "commit":
                au = (j.get("commit") or {}).get("author") or {}
                prov.update({"sha": j.get("sha"), "author": au.get("name"), "date": au.get("date"),
                             "message": ((j.get("commit") or {}).get("message") or "")[:200]})
                summary = f"commit {prov['sha']} by {prov['author']} @ {prov['date']}: {prov['message']}"
            elif ptype == "pull":
                prov.update({"number": j.get("number"), "author": (j.get("user") or {}).get("login"),
                             "merged_at": j.get("merged_at"), "sha": j.get("merge_commit_sha"),
                             "title": (j.get("title") or "")[:120], "state": j.get("state")})
                summary = f"PR #{prov['number']} '{prov['title']}' by {prov['author']} state={prov['state']} merged={prov['merged_at']} sha={prov['sha']}"
            else:
                prov.update({"tag": j.get("tag_name"), "name": j.get("name"), "date": j.get("published_at"),
                             "author": (j.get("author") or {}).get("login")})
                summary = f"release {prov['tag']} '{prov['name']}' by {prov['author']} @ {prov['date']}"
            raw, cs = summary.encode("utf-8"), "OBSERVED"
        except Exception:
            raw, cs = r["body"], "UNEXPECTED_CONTENT"
    return _res(ts, cs, r["status"], "application/vnd.github+json", raw if ts == "SUCCESS" else None, prov)


def fetch(leg):
    ac = leg["adapter_class"]
    if ac == "ACQ_HTTP_STATIC":
        return fetch_http_static(leg)
    if ac == "ACQ_GITHUB":
        return fetch_github(leg)
    if ac == "ACQ_GITHUB_SEARCH":
        return fetch_github_search(leg)
    if ac == "ACQ_GITHUB_ISSUE":
        return fetch_github_issue(leg)
    if ac == "ACQ_GITHUB_PROV":
        return fetch_github_prov(leg)
    raise ValueError(f"no live adapter for {ac} (ACQ_MANUAL は injected content を使う)")
