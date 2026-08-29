#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo "科研成果管理系统 - 更新站点脚本"
echo "=============================================="
echo "作用：把本地的数据修改（数据库 + 新增附件）提交并推送到"
echo "GitHub，Render 检测到推送后会自动重新部署，网站更新。"
echo

if [ -z "$(git status --porcelain)" ]; then
  echo "未检测到任何改动，站点已是最新。"
  exit 0
fi

echo "变更内容："
git status --porcelain | head -20

echo
echo "提交并推送..."
git add -A
git commit -m "update: 数据更新 $(date +%Y-%m-%d_%H:%M)"

for i in 1 2 3; do
  if git push origin main 2>/dev/null; then
    echo
    echo "✅ 推送成功！Render 正在自动重新部署（约 1-2 分钟生效）。"
    echo "   刷新 https://research-manager-fimd.onrender.com 即可看到最新数据。"
    exit 0
  fi
  echo "  推送失败（网络问题），重试 $i/3 ..."
  sleep 4
done

echo
echo "⚠️  推送失败。请检查网络后手动执行："
echo "    git add -A && git commit -m 'update' && git push origin main"
exit 1
