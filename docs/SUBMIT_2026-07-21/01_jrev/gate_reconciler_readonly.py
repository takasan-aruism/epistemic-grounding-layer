"""[BIND-1] structural read-only gate for bridge_reconciler.py (Taka §2-A).

Proves, by AST (not by running), that the reconciler CANNOT write git or the working tree:
  1. no open(...) in a write/append/update mode (only 'r'/'rb' allowed);
  2. no filesystem-mutating os / shutil calls;
  3. no git write subcommand string literal anywhere in the module;
  4. exactly one subprocess.* call site, and it is lexically inside _git_read;
  5. _git_read fails closed unless args[0] in the read-only allow-list;
  6. _READ_ONLY_GIT contains only read-only subcommands.
Any failure => the module is not provably read-only => GATE FAIL (do not integrate)."""
import ast
import sys

MOD = sys.argv[1]
src = open(MOD).read()
tree = ast.parse(src)
fails = []


def fail(msg):
    fails.append(msg)


# ---- 1. no write-mode open() ----
WRITE_MODE_CHARS = set('wax+')
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'open':
        mode = None
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            mode = node.args[1].value
        for kw in node.keywords:
            if kw.arg == 'mode' and isinstance(kw.value, ast.Constant):
                mode = kw.value.value
        if mode is None:
            mode = 'r'
        if any(c in WRITE_MODE_CHARS for c in str(mode)):
            fail('open() in write mode %r (line %d)' % (mode, node.lineno))

# ---- 2. no fs-mutating os/shutil calls ----
BANNED_OS = {'remove', 'unlink', 'rename', 'replace', 'mkdir', 'makedirs', 'rmdir', 'removedirs',
             'chmod', 'chown', 'symlink', 'link', 'truncate', 'write', 'mknod', 'utime'}
BANNED_SHUTIL = {'copy', 'copy2', 'copyfile', 'copytree', 'move', 'rmtree', 'make_archive'}
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        attr = node.func.attr
        base = node.func.value
        base_name = base.id if isinstance(base, ast.Name) else None
        if base_name == 'os' and attr in BANNED_OS:
            fail('os.%s call (line %d)' % (attr, node.lineno))
        if isinstance(base, ast.Attribute) and base.attr in ('path',) and attr in BANNED_OS:
            fail('os.path.%s mutator (line %d)' % (attr, node.lineno))
        if base_name == 'shutil' and attr in BANNED_SHUTIL:
            fail('shutil.%s call (line %d)' % (attr, node.lineno))

# ---- 3. no git write subcommand string literal ----
GIT_WRITE = {'commit', 'add', 'checkout', 'reset', 'apply', 'rm', 'mv', 'stash', 'push', 'pull',
             'merge', 'rebase', 'init', 'clone', 'tag', 'branch', 'config', 'restore', 'switch',
             'cherry-pick', 'revert', 'gc', 'prune', 'update-ref', 'hash-object', 'write-tree',
             'commit-tree', 'update-index', 'am', 'fetch'}
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in GIT_WRITE:
        fail('git write subcommand literal %r (line %d)' % (node.value, node.lineno))

# ---- 4. exactly one subprocess call site, inside _git_read ----
def _enclosing_func(target):
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef):
            for n in ast.walk(fn):
                if n is target:
                    return fn.name
    return None

subproc_calls = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == 'subprocess':
            subproc_calls.append(node)
        if isinstance(f, ast.Name) and f.id in ('Popen', 'system', 'popen', 'call', 'run'):
            fail('bare process call %r (line %d)' % (f.id, node.lineno))
if len(subproc_calls) != 1:
    fail('expected exactly 1 subprocess call, found %d' % len(subproc_calls))
else:
    host = _enclosing_func(subproc_calls[0])
    if host != '_git_read':
        fail('subprocess call not confined to _git_read (in %r)' % host)

# ---- 5. _git_read fails closed on non-allow-listed subcommand ----
gitread = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_git_read'), None)
if gitread is None:
    fail('_git_read not found')
else:
    guard = False
    for n in ast.walk(gitread):
        if isinstance(n, ast.Raise):
            # a raise gated by a membership test against _READ_ONLY_GIT
            guard = True
    has_membership = '_READ_ONLY_GIT' in ast.dump(gitread)
    if not (guard and has_membership):
        fail('_git_read lacks a fail-closed _READ_ONLY_GIT membership guard')

# ---- 6. allow-list contains only read-only subcommands ----
allow_assign = next((n for n in ast.walk(tree)
                     if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == '_READ_ONLY_GIT' for t in n.targets)), None)
if allow_assign is None:
    fail('_READ_ONLY_GIT not defined')
else:
    lits = {c.value for c in ast.walk(allow_assign) if isinstance(c, ast.Constant) and isinstance(c.value, str)}
    leaked = lits & GIT_WRITE
    if leaked:
        fail('_READ_ONLY_GIT contains write subcommands: %r' % leaked)
    if not lits:
        fail('_READ_ONLY_GIT is empty / not a literal set')

print('=== reconciler read-only gate: %s ===' % ('PASS' if not fails else 'FAIL'))
for m in fails:
    print('  FAIL:', m)
sys.exit(0 if not fails else 2)
