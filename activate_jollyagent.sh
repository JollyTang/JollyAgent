#!/bin/bash
# JollyAgent 环境激活脚本

# 获取脚本所在目录（JollyAgent项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 激活虚拟环境
source "$SCRIPT_DIR/.venv/bin/activate"

# 设置别名（如果还没有设置的话）
if ! alias jollyagent 2>/dev/null; then
    alias jollyagent="$SCRIPT_DIR/.venv/bin/jollyagent"
fi

echo "JollyAgent 环境已激活！"
echo "你现在可以在任何目录使用 'jollyagent' 命令了。"
echo "项目目录: $SCRIPT_DIR" 