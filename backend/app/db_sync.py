import os
import base64
import httpx
import shutil
import sqlite3
import tempfile
import threading
import time

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://afjfieukktcjxgvtawjy.supabase.co")
_key_b64 = os.getenv("SUPABASE_SERVICE_KEY_B64", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or (base64.b64decode(_key_b64).decode() if _key_b64 else "")
BUCKET_NAME = "attachments"
DB_STORAGE_PATH = "database/research_manager.db"
LOCAL_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "research_manager.db")
LOCAL_DB_PATH = os.path.abspath(LOCAL_DB_PATH)

_CORE_TABLES = ("papers", "books", "projects", "awards", "attachments")

_upload_lock = threading.Lock()
_pending_upload = False
_upload_timer = None


def _headers():
    return {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
    }


def _db_stats(path):
    result = {"exists": False, "usable": False, "total": 0, "tables": {}, "reason": ""}
    if not path or not os.path.exists(path):
        result["reason"] = "no file"
        return result
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            missing = [t for t in _CORE_TABLES if t not in tables]
            if missing:
                result["reason"] = f"missing tables: {missing}"
                return result
            for t in _CORE_TABLES:
                result["tables"][t] = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            result["total"] = sum(result["tables"].values())
            result["exists"] = True
            result["usable"] = result["total"] > 0
            result["reason"] = "" if result["usable"] else "empty db (0 rows)"
            return result
        finally:
            conn.close()
    except Exception as e:
        result["reason"] = f"error: {e}"
        return result


def _validate_db_bytes(content):
    if len(content) <= 100:
        return False, {"reason": "too small", "total": 0}
    fd, tmp = tempfile.mkstemp(suffix=".db")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        stats = _db_stats(tmp)
        return stats["usable"], stats
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def download_db():
    if not SUPABASE_KEY:
        return False
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{DB_STORAGE_PATH}"
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, headers=_headers())
            if resp.status_code != 200:
                print(f"[db_sync] No DB in Supabase (status={resp.status_code}), keeping local")
                return False
            remote_ok, remote_stats = _validate_db_bytes(resp.content)
            if not remote_ok:
                print(f"[db_sync] Remote DB invalid ({remote_stats['reason']}), keeping local")
                return False

            local_stats = _db_stats(LOCAL_DB_PATH)
            if local_stats["usable"] and local_stats["total"] > remote_stats["total"]:
                print(
                    f"[db_sync] Local DB has more rows ({local_stats['total']}) than "
                    f"remote ({remote_stats['total']}), keeping local"
                )
                return False
            if local_stats["exists"]:
                try:
                    shutil.copy2(LOCAL_DB_PATH, LOCAL_DB_PATH + ".bak")
                except OSError:
                    pass
            with open(LOCAL_DB_PATH, "wb") as f:
                f.write(resp.content)
            print(f"[db_sync] Downloaded DB from Supabase ({len(resp.content)} bytes, rows={remote_stats['total']})")
            return True
    except Exception as e:
        print(f"[db_sync] Download failed: {e}, keeping local")
        return False


def upload_db():
    if not SUPABASE_KEY:
        return False
    if not os.path.exists(LOCAL_DB_PATH):
        return False
    stats = _db_stats(LOCAL_DB_PATH)
    if not stats["usable"] and os.getenv("ALLOW_EMPTY_DB_UPLOAD") != "true":
        print(
            f"[db_sync] REFUSING to upload empty/invalid DB ({stats['reason']}). "
            "Data-loss guard active. Set ALLOW_EMPTY_DB_UPLOAD=true to override."
        )
        return False
    try:
        with open(LOCAL_DB_PATH, "rb") as f:
            content = f.read()
        with httpx.Client(timeout=60) as client:
            url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{DB_STORAGE_PATH}"
            resp = client.post(
                url,
                headers={**_headers(), "Content-Type": "application/octet-stream", "x-upsert": "true"},
                content=content,
            )
            if resp.status_code in (200, 201):
                print(f"[db_sync] Uploaded DB to Supabase ({len(content)} bytes)")
                return True
            print(f"[db_sync] Upload failed: {resp.status_code} {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"[db_sync] Upload failed: {e}")
        return False


def _do_deferred_upload():
    global _pending_upload
    with _upload_lock:
        _pending_upload = False
    upload_db()


def schedule_upload():
    global _pending_upload, _upload_timer
    with _upload_lock:
        _pending_upload = True
        if _upload_timer is not None:
            _upload_timer.cancel()
        _upload_timer = threading.Timer(2.0, _do_deferred_upload)
        _upload_timer.daemon = True
        _upload_timer.start()
