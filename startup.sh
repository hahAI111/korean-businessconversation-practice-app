#!/bin/bash
# Azure App Service 启动脚本
cd /home/site/wwwroot

echo "[STARTUP] Checking environment..."
echo "[STARTUP] Contents of /home/site/wwwroot:"
ls -la /home/site/wwwroot/

# 安装系统依赖（zstd 解压 + ffmpeg 语音转码）
echo "[STARTUP] Installing system dependencies..."
apt-get update -qq && apt-get install -y -qq zstd ffmpeg > /dev/null 2>&1 || true

# 如果 antenv 不存在但 output.tar.zst 存在，解压它
if [ ! -d "antenv" ] && [ -f "output.tar.zst" ]; then
    echo "[STARTUP] Extracting compressed build output..."
    tar --zstd -xf output.tar.zst
    echo "[STARTUP] Extraction complete."
fi

echo "[STARTUP] ffmpeg: $(which ffmpeg 2>/dev/null || echo 'not found')"

# 验证 antenv 存在
if [ ! -d "antenv" ]; then
    echo "[STARTUP] ERROR: antenv not found! Oryx build may have failed."
    echo "[STARTUP] Listing all directories:"
    find /home/site/wwwroot -maxdepth 1 -type d
    exit 1
fi

# 激活虚拟环境
echo "[STARTUP] Activating antenv..."
source antenv/bin/activate

# 验证关键包可用
python -c "import uvicorn; import fastapi; print('[STARTUP] Packages OK: uvicorn + fastapi')" || {
    echo "[STARTUP] ERROR: Required packages not found in antenv!"
    pip list 2>&1 | head -20
    exit 1
}

echo "[STARTUP] Starting uvicorn (2 workers)..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
