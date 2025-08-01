#!/bin/bash
# JollyAgent 环境激活脚本

# 获取脚本所在目录（JollyAgent项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查虚拟环境是否存在
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv "$SCRIPT_DIR/.venv"
    echo "虚拟环境创建完成！"
fi

# 激活虚拟环境
source "$SCRIPT_DIR/.venv/bin/activate"

# 检查项目是否已安装
if ! python -c "import jollyagent" 2>/dev/null; then
    echo "正在安装JollyAgent项目..."
    pip install -e "$SCRIPT_DIR"
    echo "项目安装完成！"
fi

# 设置别名（如果还没有设置的话）
if ! alias jollyagent 2>/dev/null >/dev/null; then
    alias jollyagent="$SCRIPT_DIR/.venv/bin/jollyagent"
fi

echo "JollyAgent 环境已激活！"
echo "你现在可以在任何目录使用 'jollyagent' 命令了。"
echo "项目目录: $SCRIPT_DIR"
echo ""
echo "可用命令："
echo "  jollyagent start    - 启动交互式模式"
echo "  jollyagent chat     - 开始对话"
echo "  jollyagent config   - 查看配置"
echo "  jollyagent help     - 查看帮助" 