import os
import base64
import httpx
import shutil
import threading
import time

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://afjfieukktcjxgvtawjy.supabase.co")
_key_b64 = os.getenv("SUPABASE_SERVICE_KEY_B64", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or (base64.b64decode(_key_b64).decode() if _key_b64 else "")
BUCKET_NAME = "attachments"
DB_STORAGE_PATH = "database/research_manager.db"
LOCAL_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "research_manager.db")
LOCAL_DB_PATH = os.path.abspath(LOCAL_DB_PATH)

_upload_lock = threading.Lock()
_pending_upload = False
_upload_timer = None


def _headers():
    return {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
    }


def download_db():
    if not SUPABASE_KEY:
        return False
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{DB_STORAGE_PATH}"
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, headers=_headers())
            if resp.status_code == 200 and len(resp.content) > 100:
                with open(LOCAL_DB_PATH, "wb") as f:
                    f.write(resp.content)
                print(f"[db_sync] Downloaded DB from Supabase ({len(resp.content)} bytes)")
                return True
            else:
                print(f"[db_sync] No DB in Supabase (status={resp.status_code}), using local")
                return False
    except Exception as e:
        print(f"[db_sync] Download failed: {e}, using local")
        return False


def upload_db():
    if not SUPABASE_KEY:
        return False
    if not os.path.exists(LOCAL_DB_PATH):
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
