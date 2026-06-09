import os
from pathlib import Path

PROJECT_DIR = Path(__file__).parent

import uvicorn
from app.core.logger import get_logger

logger = get_logger(service="server")

def start_server():
    # 确保工作目录正确
    os.chdir(PROJECT_DIR)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    
    logger.info("Starting server...")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(
        f"Uvicorn config: host={host}, port={port}, reload={reload_enabled}"
    )
    
    uvicorn.run(
        "main:app",        # 使用模块路径
        host=host,
        port=port,
        access_log=False,
        log_level="info",
        reload=reload_enabled
    )

if __name__ == "__main__":
    start_server() 
