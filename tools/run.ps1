# LLM代码生成平台 - PowerShell启动脚本
# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "LLM代码生成平台 - 启动器"

# 设置错误处理
$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
}

function Test-Command {
    param([string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Install-Dependencies {
    Write-ColorOutput "📦 检查并安装Python依赖..." "Yellow"
    
    try {
        & python -m pip install --upgrade pip
        & python -m pip install -r requirements.txt
        Write-ColorOutput "✅ 依赖安装完成" "Green"
        return $true
    } catch {
        Write-ColorOutput "❌ 依赖安装失败: $_" "Red"
        return $false
    }
}

function Test-Configuration {
    Write-ColorOutput "🔧 检查配置文件..." "Yellow"
    
    if (-not (Test-Path "config.json")) {
        Write-ColorOutput "❌ 错误：未找到config.json配置文件" "Red"
        Write-ColorOutput "请参考README.md配置API密钥" "Yellow"
        return $false
    }
    
    try {
        $config = Get-Content "config.json" | ConvertFrom-Json
        $providerCount = $config.providers.Count
        Write-ColorOutput "✅ 配置文件有效，包含 $providerCount 个AI提供者" "Green"
        return $true
    } catch {
        Write-ColorOutput "❌ 配置文件格式错误: $_" "Red"
        return $false
    }
}

function Start-Services {
    Write-ColorOutput "🚀 启动LLM代码生成平台..." "Green"
    Write-ColorOutput "📱 前端界面将在: http://localhost:8080" "Cyan"
    Write-ColorOutput "🔧 后端API将在: http://localhost:8000" "Cyan"
    Write-ColorOutput "📚 API文档将在: http://localhost:8000/docs" "Cyan"
    Write-Host ""
    Write-ColorOutput "按 Ctrl+C 停止服务" "Yellow"
    Write-Host ""
    
    try {
        & python scripts/start.py
    } catch {
        Write-ColorOutput "❌ 服务启动失败: $_" "Red"
        return $false
    }
}

function Initialize-Environment {
    Write-ColorOutput "🔧 初始化Python虚拟环境..." "Yellow"
    
    # 检查是否存在虚拟环境
    if (-not (Test-Path ".venv")) {
        Write-ColorOutput "📦 创建虚拟环境..." "Yellow"
        try {
            & python -m venv .venv
            Write-ColorOutput "✅ 虚拟环境创建成功" "Green"
        } catch {
            Write-ColorOutput "❌ 虚拟环境创建失败: $_" "Red"
            return $false
        }
    }
    
    # 激活虚拟环境
    Write-ColorOutput "🔧 激活虚拟环境..." "Yellow"
    $activateScript = ".venv\Scripts\Activate.ps1"
    
    if (Test-Path $activateScript) {
        try {
            & $activateScript
            Write-ColorOutput "✅ 虚拟环境已激活" "Green"
            return $true
        } catch {
            Write-ColorOutput "❌ 虚拟环境激活失败: $_" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "❌ 找不到虚拟环境激活脚本" "Red"
        return $false
    }
}

# 主程序开始
try {
    Write-Header "🎯 LLM代码生成平台 - PowerShell启动器"
    
    # 检查Python
    Write-ColorOutput "🐍 检查Python环境..." "Yellow"
    if (-not (Test-Command "python")) {
        Write-ColorOutput "❌ 错误：未找到Python，请先安装Python 3.8+" "Red"
        Write-ColorOutput "下载地址：https://www.python.org/downloads/" "Cyan"
        Read-Host "按回车键退出"
        exit 1
    }
    
    $pythonVersion = & python --version
    Write-ColorOutput "✅ 发现Python: $pythonVersion" "Green"
    
    # 检查项目结构
    Write-ColorOutput "📁 检查项目结构..." "Yellow"
    $requiredPaths = @("backend", "scripts", "requirements.txt")
    foreach ($path in $requiredPaths) {
        if (-not (Test-Path $path)) {
            Write-ColorOutput "❌ 错误：未找到必需的文件或目录: $path" "Red"
            Read-Host "按回车键退出"
            exit 1
        }
    }
    Write-ColorOutput "✅ 项目结构检查通过" "Green"
    
    # 初始化环境
    if (-not (Initialize-Environment)) {
        Read-Host "按回车键退出"
        exit 1
    }
    
    # 安装依赖
    if (-not (Install-Dependencies)) {
        Read-Host "按回车键退出"
        exit 1
    }
    
    # 检查配置
    if (-not (Test-Configuration)) {
        Read-Host "按回车键退出"
        exit 1
    }
    
    # 启动服务
    Write-Header "🚀 启动服务"
    Start-Services
    
} catch {
    Write-ColorOutput "💥 启动过程中发生错误: $_" "Red"
    Write-ColorOutput "请检查错误信息并重试" "Yellow"
} finally {
    Write-Host ""
    Write-ColorOutput "👋 启动器退出" "Yellow"
    Read-Host "按回车键关闭窗口"
}
