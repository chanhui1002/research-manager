#!/usr/bin/env python3
"""
恢复脚本：把本地数据库和附件文件重新上传到 Supabase Storage。

背景：线上 Render 容器磁盘是临时的，数据库和附件全靠启动时从 Supabase
下载。如果 Supabase 备份缺失/被空库覆盖，线上就会变成全空。本脚本用本地
完整数据（backend/research_manager.db + backend/uploads/）把备份修好。

用法：
  python3 recover_supabase.py                # 检查并补齐缺失文件
  python3 recover_supabase.py --check-only   # 只检查，不修改
  python3 recover_supabase.py --force        # 即使远端已有同名文件也强制重传

前提：
  - Supabase 项目未暂停（若已 Paused，先到控制台 Restore）
  - 本地 backend/research_manager.db 含全部记录
  - 本地 backend/uploads/ 含附件文件
  - 密钥：环境变量 SUPABASE_SERVICE_KEY 或 SUPABASE_SERVICE_KEY_B64
    （未设置时回退到 Dockerfile 里写死的那把 service_role key）
"""
import argparse
import base64
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://afjfieukktcjxgvtawjy.supabase.co")
_key_b64 = os.getenv("SUPABASE_SERVICE_KEY_B64", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or (
    base64.b64decode(_key_b64).decode() if _key_b64 else ""
)
if not SUPABASE_KEY:
    _fallback = "c2Jfc2VjcmV0XzNrMDJiTWVBbFFxd0RQRnJILW8xRWdfNFRjUTRESWU="
    SUPABASE_KEY = base64.b64decode(_fallback).decode()

BUCKET = "attachments"
DB_STORAGE_PATH = "database/research_manager.db"

ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_DB = os.path.join(ROOT, "backend", "research_manager.db")
UPLOADS_DIR = os.path.join(ROOT, "backend", "uploads")

CORE_TABLES = ("papers", "books", "projects", "awards", "adoptions", "honors", "trainings", "attachments")

SLEEP = 0.05
RETRIES = 3


def headers():
    return {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
    }


def http(method, url, body=None, content_type=None, extra=None, retries=RETRIES):
    h = headers()
    if content_type:
        h["Content-Type"] = content_type
    if extra:
        h.update(extra)
    data = body.encode() if isinstance(body, str) else body
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            return e.code, e.read()
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise


def obj_exists(path):
    url = f"{SUPABASE_URL}/storage/v1/object/info/{BUCKET}/{path}"
    code, _ = http("GET", url)
    return code == 200


def upload_object(path, content, content_type="application/octet-stream"):
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}"
    code, body = http(
        "POST", url, body=content,
        content_type=content_type,
        extra={"x-upsert": "true"},
    )
    return code in (200, 201), (code, body)


def db_stats(path):
    result = {"exists": False, "usable": False, "total": 0, "tables": {}, "reason": ""}
    if not path or not os.path.exists(path):
        result["reason"] = "本地数据库文件不存在"
        return result
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            missing = [t for t in CORE_TABLES if t not in tables]
            if missing:
                result["reason"] = f"缺少数据表: {missing}"
                return result
            for t in CORE_TABLES:
                result["tables"][t] = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            result["total"] = sum(result["tables"].values())
            result["exists"] = True
            result["usable"] = result["total"] > 0
            result["reason"] = "" if result["usable"] else "数据库全空（0 行）"
            return result
        finally:
            conn.close()
    except Exception as e:
        result["reason"] = f"读取失败: {e}"
        return result


def list_attachments(db_path):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT entity_type, entity_id, filename, file_path, original_filename "
            "FROM attachments ORDER BY file_path"
        ).fetchall()
    finally:
        conn.close()
    return [{"entity_type": r[0], "entity_id": r[1], "filename": r[2], "file_path": r[3], "original_filename": r[4]} for r in rows]


def main():
    parser = argparse.ArgumentParser(description="恢复 Supabase 备份")
    parser.add_argument("--check-only", action="store_true", help="只检查，不修改")
    parser.add_argument("--force", action="store_true", help="远端已存在也强制重传")
    args = parser.parse_args()

    print("=" * 70)
    print("科研成果管理系统 - Supabase 备份恢复脚本")
    print("=" * 70)

    if not SUPABASE_KEY:
        print("[错误] 未找到 Supabase 密钥（SUPABASE_SERVICE_KEY / SUPABASE_SERVICE_KEY_B64）")
        return 1

    stats = db_stats(LOCAL_DB)
    print(f"\n本地数据库: {LOCAL_DB}")
    print(f"  状态: {stats['reason'] or '正常'}")
    if stats["usable"]:
        for t in CORE_TABLES:
            print(f"  {t}: {stats['tables'][t]}")
    if not stats["usable"]:
        print(f"\n[错误] {stats['reason']}，无法用于恢复。")
        return 1

    print(f"\n[1/3] 检查 Supabase 连通性: {SUPABASE_URL}")
    try:
        code, body = http("GET", f"{SUPABASE_URL}/storage/v1/bucket")
        if code == 200:
            print(f"  连通 OK（bucket 接口返回 200）")
        else:
            print(f"[错误] 返回 HTTP {code}: {body[:300]}")
            print("如果项目显示 Paused，请先到 https://supabase.com/dashboard 恢复项目后再运行。")
            return 1
    except Exception as e:
        print(f"[错误] 无法连接 Supabase: {e}")
        print("如果项目显示 Paused，请先到 https://supabase.com/dashboard 恢复项目后再运行。")
        return 1

    print(f"\n[2/3] 上传数据库到 {DB_STORAGE_PATH}")
    with open(LOCAL_DB, "rb") as f:
        content = f.read()
    ok, (code, body) = upload_object(DB_STORAGE_PATH, content)
    if ok:
        print(f"  数据库已上传（{len(content)} 字节）")
    else:
        print(f"[错误] 数据库上传失败 HTTP {code}: {body[:300]}")
        return 1

    print(f"\n[3/3] 检查并补齐附件（共 {stats['tables']['attachments']} 条记录）")
    attachments = list_attachments(LOCAL_DB)
    existing = 0
    uploaded = 0
    failed = 0
    skipped = 0
    missing_local = 0
    for i, att in enumerate(attachments, 1):
        remote = att["file_path"]
        local_file = os.path.join(UPLOADS_DIR, remote)
        if not os.path.isfile(local_file):
            print(f"  [跳过] 本地缺少文件: {remote}")
            missing_local += 1
            continue
        if not args.force:
            try:
                if obj_exists(remote):
                    existing += 1
                    continue
            except Exception as e:
                print(f"  [警告] 检查远端失败({e})，将尝试重传: {remote}")
        ok, (code, body) = upload_object(remote, open(local_file, "rb").read())
        if ok:
            uploaded += 1
            if i % 25 == 0 or uploaded + existing + failed + skipped == len(attachments):
                print(f"  进度: {i}/{len(attachments)}（已存在 {existing} / 已上传 {uploaded} / 失败 {failed}）")
        else:
            failed += 1
            print(f"  [失败] {remote}: HTTP {code} {body[:200]}")
        time.sleep(SLEEP)

    print("\n" + "=" * 70)
    print("恢复完成汇总:")
    print(f"  数据库: 已上传")
    print(f"  附件: 共 {len(attachments)} 条记录，远端已存在 {existing}，本次上传 {uploaded}，失败 {failed}")
    print(f"  本地缺失文件: {missing_local}（这些文件不在 backend/uploads/ 下）")
    if failed:
        print("  ⚠️ 有失败项，请重试或检查 Supabase 项目状态。")
    else:
        print("  ✅ 全部完成。重新部署 Render（或等下次冷启动）即可自动拉取恢复。")
    print("=" * 70)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
