#!/usr/bin/env python3
"""
一键同步脚本：把本地数据库和附件文件上传到 Supabase Storage。

用于把系统数据迁移/备份到（新的）Supabase 项目。线上站点切换到 Supabase
存储时，在 Render 环境变量设置：
  ATTACHMENT_STORAGE=supabase
  SUPABASE_URL=https://<你的项目ref>.supabase.co
  SUPABASE_SERVICE_KEY=服务端密钥(service_role key)

用法：
  python3 recover_supabase.py --url <PROJECT_URL> --key <SERVICE_KEY>
  python3 recover_supabase.py --url <PROJECT_URL> --key-b64 <BASE64_KEY>
  python3 recover_supabase.py --url <PROJECT_URL>            # 密钥从环境变量读取
  python3 recover_supabase.py --url ... --key ... --check-only
  python3 recover_supabase.py --url ... --key ... --force
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

BUCKET = "attachments"
DB_STORAGE_PATH = "database/research_manager.db"

ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_DB = os.path.join(ROOT, "backend", "research_manager.db")
UPLOADS_DIR = os.path.join(ROOT, "backend", "uploads")

CORE_TABLES = ("papers", "books", "projects", "awards", "adoptions", "honors", "trainings", "attachments")

SLEEP = 0.05
RETRIES = 3


def resolve_key(args):
    if args.key:
        return args.key
    if args.key_b64:
        return base64.b64decode(args.key_b64).decode()
    if os.getenv("SUPABASE_SERVICE_KEY"):
        return os.getenv("SUPABASE_SERVICE_KEY")
    if os.getenv("SUPABASE_SERVICE_KEY_B64"):
        return base64.b64decode(os.getenv("SUPABASE_SERVICE_KEY_B64")).decode()
    return ""


def http(method, url, key, body=None, content_type=None, extra=None, retries=RETRIES):
    h = {"Authorization": f"Bearer {key}", "apikey": key}
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


def obj_exists(url, key, path):
    code, _ = http("GET", f"{url}/storage/v1/object/info/{BUCKET}/{path}", key)
    return code == 200


def upload_object(url, key, path, content, content_type="application/octet-stream"):
    code, body = http(
        "POST", f"{url}/storage/v1/object/{BUCKET}/{path}", key,
        body=content, content_type=content_type, extra={"x-upsert": "true"},
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
    parser = argparse.ArgumentParser(description="同步本地数据到 Supabase Storage")
    parser.add_argument("--url", required=True, help="Supabase 项目地址，如 https://xxxx.supabase.co")
    parser.add_argument("--key", default="", help="service_role 密钥")
    parser.add_argument("--key-b64", default="", help="service_role 密钥（base64 编码）")
    parser.add_argument("--check-only", action="store_true", help="只检查，不上传")
    parser.add_argument("--force", action="store_true", help="远端已存在也强制重传")
    args = parser.parse_args()

    url = args.url.rstrip("/")
    key = resolve_key(args)
    if not key:
        print("[错误] 未提供密钥。用 --key / --key-b64 传入，或设置环境变量 SUPABASE_SERVICE_KEY")
        return 1

    print("=" * 70)
    print("科研成果管理系统 - Supabase 数据同步")
    print("=" * 70)
    print(f"目标项目: {url}")

    stats = db_stats(LOCAL_DB)
    print(f"\n本地数据库: {LOCAL_DB}")
    print(f"  状态: {stats['reason'] or '正常'}")
    if stats["usable"]:
        for t in CORE_TABLES:
            print(f"  {t}: {stats['tables'][t]}")
    if not stats["usable"]:
        print(f"\n[错误] {stats['reason']}，无法同步。")
        return 1

    print(f"\n[1/3] 检查 Supabase 连通性")
    try:
        code, body = http("GET", f"{url}/storage/v1/bucket", key)
        if code == 200:
            print("  连通 OK")
        else:
            print(f"[错误] 返回 HTTP {code}: {body[:300]}")
            print("若项目显示 Paused，请先到 https://supabase.com/dashboard 恢复项目。")
            return 1
    except Exception as e:
        print(f"[错误] 无法连接 Supabase: {e}")
        print("若项目显示 Paused，请先到 https://supabase.com/dashboard 恢复项目。")
        return 1

    if not args.check_only:
        print(f"\n[2/3] 上传数据库到 {DB_STORAGE_PATH}")
        with open(LOCAL_DB, "rb") as f:
            content = f.read()
        ok, (code, body) = upload_object(url, key, DB_STORAGE_PATH, content)
        if ok:
            print(f"  数据库已上传（{len(content)} 字节）")
        else:
            print(f"[错误] 数据库上传失败 HTTP {code}: {body[:300]}")
            return 1

    print(f"\n[3/3] 附件检查（共 {stats['tables']['attachments']} 条记录）")
    attachments = list_attachments(LOCAL_DB)
    existing = 0
    uploaded = 0
    failed = 0
    missing_local = 0
    for i, att in enumerate(attachments, 1):
        remote = att["file_path"]
        local_file = os.path.join(UPLOADS_DIR, remote)
        if not os.path.isfile(local_file):
            missing_local += 1
            continue
        if not args.force:
            try:
                if obj_exists(url, key, remote):
                    existing += 1
                    continue
            except Exception as e:
                print(f"  [警告] 检查远端失败({e})，将尝试重传: {remote}")
        if args.check_only:
            uploaded += 1
            continue
        with open(local_file, "rb") as f:
            content = f.read()
        ok, (code, body) = upload_object(url, key, remote, content)
        if ok:
            uploaded += 1
        else:
            failed += 1
            print(f"  [失败] {remote}: HTTP {code} {body[:200]}")
        if (uploaded + existing + failed) % 25 == 0 or i == len(attachments):
            print(f"  进度: {i}/{len(attachments)}（已存在 {existing} / 已上传 {uploaded} / 失败 {failed}）")
        time.sleep(SLEEP)

    print("\n" + "=" * 70)
    mode = "检查完成" if args.check_only else "同步完成"
    print(f"{mode}汇总:")
    print(f"  数据库: {'将上传' if args.check_only else '已上传'}")
    print(f"  附件: 共 {len(attachments)} 条记录，远端已存在 {existing}，本次上传 {uploaded}，失败 {failed}")
    print(f"  本地缺失文件: {missing_local}")
    if failed:
        print("  ⚠️ 有失败项，请重试或检查 Supabase 项目状态。")
    elif not args.check_only:
        print("  ✅ 全部完成。确认 Render 环境变量（ATTACHMENT_STORAGE=supabase 等）后即可切换。")
    print("=" * 70)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
