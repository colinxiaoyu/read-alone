#!/bin/bash
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v node >/dev/null || ! command -v npm >/dev/null; then
  echo "请安装 Node.js 20.19+ 或 22.12+ 后重新打开。"
  read -r -p "按回车键关闭。"
  exit 1
fi
npm start
