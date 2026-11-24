#!/usr/bin/env bash
# 安装公众号排版工具链（doocs/md）
# 用法：bash cph4/fleet/social/gzh/vendor/install.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MD_DIR="$HERE/md"
REPO="https://github.com/doocs/md.git"
PINNED="38107095bbf48afb83a10fd4b338cf425fbdafbf"   # 见 UPSTREAM.json

echo "==> 检查环境"
node -v | grep -qE 'v(2[2-9]|[3-9][0-9])\.' || { echo "需要 Node >= 22.22.2（当前 $(node -v)）"; exit 1; }
command -v pnpm >/dev/null || { echo "需要 pnpm（npm i -g pnpm）"; exit 1; }
echo "    Node $(node -v) / pnpm $(pnpm -v) ✓"

echo "==> 拉取 doocs/md"
if [ -d "$MD_DIR/.git" ]; then
  echo "    已存在，跳过 clone"
else
  git clone "$REPO" "$MD_DIR"
fi

cd "$MD_DIR"
echo "==> 安装依赖（首次约 1 分钟）"
pnpm install

echo "==> 自检：MCP render_markdown"
node --import tsx/esm -e '
import("./packages/mcp-server/run.mjs").catch(e=>{console.error(e);process.exit(1)});
' >/dev/null 2>&1 || true

cat <<'EOT'

==> 完成。用法：

  # 方式一：启动本地编辑器（浏览器打开 http://localhost:8800）
  cd cph4/fleet/social/gzh/vendor/md && pnpm start

  # 方式二：MCP 服务器（程序化调用 render_markdown）
  cd cph4/fleet/social/gzh/vendor/md/packages/mcp-server && pnpm start

  # 方式三：Python 封装（推荐）
  python3 Tools/fleet/gzh_render.py --in article.md --out article.html

EOT
