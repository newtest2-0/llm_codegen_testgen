@echo off
chcp 65001 >nul
title LLM代码生成平台 - 一键启动

echo ====================================================
echo 🎯 LLM代码生成平台 - 一键启动器
echo ====================================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查是否存在虚拟环境
if not exist ".venv\" (
    echo 📦 正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

:: 激活虚拟环境
echo 🔧 激活虚拟环境...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)

:: 安装依赖
echo 📦 检查并安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

:: 检查配置文件
if not exist "config.json" (
    echo ❌ 错误：未找到config.json配置文件
    echo 请参考README.md配置API密钥
    pause
    exit /b 1
)

:: 启动服务
echo.
echo 🚀 启动服务中...
echo ====================================================
python scripts\start.py

:: 服务停止后的清理
echo.
echo 👋 服务已停止
pause
