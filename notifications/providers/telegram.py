import os
import json
import urllib.request
import urllib.parse
from .base import SendResult

API_BASE = "https://api.telegram.org"

def _http_get(url: str, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.status, resp.read()

def _http_post_json(url: str, payload: dict, timeout=10):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read()

def _resolve_chat_id(chat_id: str, token: str) -> tuple[str | None, str | None]:
    """
    Принимает numeric id или @username.
    Возвращает (chat_id, error).
    """
    s = (chat_id or "").strip()
    if not s:
        return None, "Missing telegram chat_id"

    if s.lstrip("-").isdigit():
        return s, None

    username = s if s.startswith("@") else f"@{s}"
    try:
        url = f"{API_BASE}/bot{token}/getChat?chat_id={urllib.parse.quote(username)}"
        status, body = _http_get(url)
        if status == 200:
            data = json.loads(body.decode("utf-8"))
            if data.get("ok") and "result" in data and "id" in data["result"]:
                return str(data["result"]["id"]), None
    except Exception as e:
        pass

    try:
        url = f"{API_BASE}/bot{token}/getUpdates"
        status, body = _http_get(url)
        if status == 200:
            data = json.loads(body.decode("utf-8"))
            if data.get("ok"):
                uname = username.lstrip("@").lower()
                for upd in data.get("result", []):
                    msg = upd.get("message") or upd.get("edited_message") or {}
                    chat = msg.get("chat") or {}
                    ch_user = (chat.get("username") or "").lower()
                    if ch_user == uname and "id" in chat:
                        return str(chat["id"]), None
        return None, "Cannot resolve @username to chat id. Ask the user to message the bot and use numeric chat_id (see getUpdates)."
    except Exception as e:
        return None, str(e)

def send_telegram(message: str, chat_id: str) -> SendResult:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return SendResult(False, error="TELEGRAM_BOT_TOKEN not set")

    real_chat_id, err = _resolve_chat_id(chat_id, token)
    if err:
        return SendResult(False, error=err)

    try:
        url = f"{API_BASE}/bot{token}/sendMessage"
        status, body = _http_post_json(url, {"chat_id": real_chat_id, "text": message})
        if 200 <= status < 300:
            try:
                payload = json.loads(body.decode("utf-8"))
                msg_id = str(payload.get("result", {}).get("message_id", "tg:ok"))
            except Exception:
                msg_id = "tg:ok"
            return SendResult(True, message_id=msg_id)
        else:
            return SendResult(False, error=f"Telegram HTTP {status}")
    except Exception as e:
        return SendResult(False, error=str(e))
