import json
import os

def create_task(item, sealed_fields=None):
    pass

def select_next():
    pass

def recompute_execution_admission(item_id, reason):
    pass

def select_and_create(token_path: str) -> dict:
    # 1. token 検証 (select_next より先)
    if not os.path.exists(token_path):
        return {"created": False, "reason": "token_not_found"}

    try:
        with open(token_path, "r") as f:
            token_data = json.load(f)
        token_id = token_data.get("token_id")
        if not token_id:
            return {"created": False, "reason": "invalid_token"}
    except Exception:
        return {"created": False, "reason": "invalid_token"}

    # 2. 再使用拒否チェック
    consumed_path = token_path + ".consumed"
    if os.path.exists(consumed_path):
        return {"created": False, "reason": "token_already_consumed"}

    # 3. select_next 実行
    selection = select_next()
    item_id = selection["item_id"]
    reason = selection["reason"]

    # 4. admission 判定 (admitted=False なら fail-closed)
    admission = recompute_execution_admission(item_id, reason)
    if not admission.get("admitted", False):
        return {"created": False, "reason": "admission_denied"}

    # 5. token 消費 (原子的 os.rename)
    try:
        os.rename(token_path, consumed_path)
    except OSError:
        return {"created": False, "reason": "token_consumption_failed"}

    # 6. create_task 呼び出し (kwarg 封印)
    sealed_fields = {
        "selected_item_id": item_id,
        "selection_reason": reason,
        "admission_recompute": admission,
        "approval_token_id": token_id,
        "actor_instance": "default",
        "producer_version": "0.3",
    }
    create_task(item={"item_id": item_id, "reason": reason}, sealed_fields=sealed_fields)

    return {"created": True, "reason": "success"}