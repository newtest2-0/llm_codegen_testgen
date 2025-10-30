# 🚀 CodeForge - 智能代码生成平台

<div align="center">

![CodeForge Logo](https://img.shields.io/badge/CodeForge-智能代码生成-blue?style=for-the-badge&logo=code&logoColor=white)

**专业的多模型代码生成、测试生成和质量评估平台**

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC?style=flat-square&logo=tailwind-css)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

## ✨ 功能特性

### 🎯 **核心功能**
- 🤖 **多模型并行生成** - 同时使用8种AI模型生成代码，提供多样化解决方案
- 🧪 **智能测试生成** - 自动为生成的代码创建完整的pytest测试用例
- 📊 **综合质量评估** - 基于BLEU-4分数、ROUGE分数、pass@k分数、测试通过率、AST质量的智能评分系统
- 🏆 **最佳方案推荐** - 自动选择综合得分最高的代码实现
- 🔄 **自动重试机制** - API调用失败时智能重试，确保服务稳定性

### 🎨 **用户界面**
- 📱 **现代化设计** - 基于Tailwind CSS的响应式界面，支持移动端
- 🕐 **历史记录管理** - 自动保存生成历史，支持重新加载和管理
- 📥 **多格式导出** - 支持ZIP、Python文件、Markdown等多种导出格式
- ⚙️ **滚动式设置** - 直观的API配置界面，支持独立保存各提供商密钥
- 🎯 **快捷操作** - 双重快捷按钮设计，提升操作效率

### 🔧 **技术特性**
- 🏗️ **简洁架构** - 清晰的前后端分离架构，易于维护和扩展
- 🚀 **高性能** - 异步处理，支持并发请求
- 🛡️ **安全可靠** - 完善的错误处理和数据验证
- 📈 **可扩展性** - 插件化的模型提供者架构，轻松添加新模型

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd llm_codegen_testgen

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate     # Windows
# 或
source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

#### 方式一：使用环境变量文件（推荐）
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的API密钥
```

#### 方式二：在Web界面中配置
启动项目后，点击右上角"设置"按钮，在滚动式API配置界面中输入密钥。

### 3. 启动服务

#### 一键启动（推荐）
```bash
# 最简单方式 - Windows用户
start.bat

# 跨平台用户
python start.py

# 高级用户 - 使用工具目录中的详细脚本
python tools/run.py        # 跨平台详细版本
tools/run.bat             # Windows批处理版本
tools/run.ps1             # PowerShell增强版本

# 首次使用建议先运行环境设置
python tools/setup.py
```

#### 传统启动方式
```bash
# 使用原始启动脚本
python scripts/start.py

# 手动启动
# 启动后端（终端1）
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（终端2）
cd web
python start_server.py
```

### 4. 访问应用

| 服务 | 地址 | 说明 |
|------|------|------|
| 🖥️ **Web界面** | http://localhost:8080 | 主要操作界面 |
| 📚 **API文档** | http://localhost:8000/docs | Swagger文档 |
| ❤️ **健康检查** | http://localhost:8000/health | 服务状态 |

## 🤖 支持的AI模型

| 提供商 | 模型 | 环境变量 | 特点 |
|--------|------|----------|------|
| 🤖 **OpenAI** | gpt-4o-mini | `OPENAI_API_KEY` | 高质量代码生成 |
| 🔍 **DeepSeek** | deepseek-chat | `DEEPSEEK_API_KEY` | 专业编程模型 |
| 🎭 **Claude** | claude-3-5-sonnet | `ANTHROPIC_API_KEY` | 代码推理能力强 |
| 💎 **Gemini** | gemini-1.5-flash | `GOOGLE_API_KEY` | 快速响应 |
| 🌟 **通义千问** | qwen-plus | `QWEN_API_KEY` | 中文友好 |
| 🏔️ **百川智能** | Baichuan4 | `BAICHUAN_API_KEY` | 国产化选择 |
| 🧠 **ChatGLM** | glm-4-plus | `CHATGLM_API_KEY` | 智谱AI |
| 🦙 **LLaMA** | llama3.1:8b | `OLLAMA_BASE_URL` | 本地部署 |

## 📖 使用指南

### 基本使用流程

1. **输入需求** - 在"项目需求"区域详细描述你的代码需求
2. **选择语言** - 选择目标编程语言（默认Python）
3. **选择模型** - 勾选要使用的AI模型（建议多选）
4. **生成代码** - 点击"生成代码"按钮开始生成
5. **查看结果** - 系统会显示各模型的生成结果和综合评分
6. **选择方案** - 查看推荐的最佳方案或选择其他方案

### 高级功能

#### 📚 历史记录管理
- **自动保存**：每次生成的结果自动保存到本地
- **重新加载**：点击历史记录可重新加载到表单
- **批量管理**：支持删除不需要的历史记录

#### 📥 代码导出
- **多种格式**：ZIP压缩包、Python文件、纯文本、Markdown
- **自定义内容**：可选择导出代码、测试用例、评测结果
- **一键下载**：生成后立即下载到本地

#### ⚙️ 系统设置
- **API管理**：滚动式界面配置各提供商API密钥
- **系统偏好**：设置默认语言、自动保存等选项
- **实时状态**：显示API配置状态和连接情况

## 🏗️ 项目架构

```
llm_codegen_testgen/
├── 🏠 backend/                 # 后端服务
│   ├── 🔌 api/                # API接口层
│   │   ├── routes/           # 路由定义
│   │   └── middleware.py     # 中间件
│   ├── 🧠 core/               # 核心模块
│   │   ├── config.py         # 配置管理
│   │   ├── providers/        # AI模型提供者
│   │   └── evaluators/       # 代码评估器
│   ├── 📋 models/             # 数据模型
│   ├── 🔧 services/           # 业务服务
│   ├── 🛠️ utils/              # 工具函数
│   └── 🚀 app.py              # 主应用入口
├── 🌐 web/                    # 前端界面
│   ├── 📄 templates/          # HTML模板
│   │   └── index.html        # 主页面
│   ├── 📦 static/             # 静态资源
│   │   └── js/main.js        # 主要逻辑
│   └── 🖥️ start_server.py     # 前端服务器
├── 📜 scripts/                # 原始启动和演示脚本
│   ├── start.py              # 原始启动脚本
│   └── demo_*.py             # 演示脚本
├── 🛠️ tools/                  # 工具和启动脚本
│   ├── run.py                # 跨平台启动脚本
│   ├── run.bat               # Windows批处理启动
│   ├── run.ps1               # PowerShell启动脚本
│   └── setup.py              # 环境设置脚本
├── 📚 docs/                   # 项目文档
│   ├── 启动说明.md             # 启动使用指南
│   ├── CHANGELOG.md          # 更新日志
│   └── CONTRIBUTING.md       # 贡献指南
├── 🚀 start.py                # 快速启动（根目录）
├── 🖱️ start.bat               # Windows快速启动
├── ⚙️ config.json             # 系统配置
├── 📝 .env.example            # 环境变量模板
├── 🚫 .gitignore              # Git忽略文件
├── 📦 requirements.txt        # Python依赖
├── 📄 LICENSE                 # 开源许可证
└── 📖 README.md               # 项目文档
```

## 🔧 配置说明

### 环境变量配置

创建 `.env` 文件并配置以下变量：

```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1

# DeepSeek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-claude-key

# Google Gemini
GOOGLE_API_KEY=your-google-api-key

# 通义千问
QWEN_API_KEY=your-qwen-key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 百川智能
BAICHUAN_API_KEY=your-baichuan-key
BAICHUAN_BASE_URL=https://api.baichuan-ai.com/v1

# ChatGLM
CHATGLM_API_KEY=your-chatglm-key
CHATGLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# Ollama (本地)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=ollama
```

### 系统配置

`config.json` 文件包含以下配置：

- **providers**: AI模型提供者配置
- **scoring**: 评分权重设置
- **enhanced_evaluation**: 增强评估配置

## 📊 评分系统

### 基础评分指标

| 指标 | 权重 | 说明 |
|------|------|------|
| **BLEU-4分数** | 35% | 代码与参考实现的相似度（使用4-gram匹配） |
| **ROUGE分数** | 15% | 代码摘要质量评估 |
| **pass@k分数** | 20% | 测试通过率评估 |
| **测试通过率** | 45% | 自动生成测试的通过情况 |
| **AST质量** | 20% | 代码结构和语法质量 |

### 增强评分指标

| 指标 | 权重 | 说明 |
|------|------|------|
| **功能性** | 35% | 代码功能完整性和正确性 |
| **代码质量** | 25% | 代码规范和最佳实践 |
| **代码风格** | 15% | 编码风格和可读性 |
| **安全性** | 15% | 安全漏洞和风险评估 |
| **可维护性** | 10% | 代码的可维护和扩展性 |

## 🔍 故障排除

### 常见问题

#### 🔴 服务启动失败
```bash
# 检查端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

#### 🔴 API调用失败
1. **检查API密钥**：确保在 `.env` 文件或Web界面中正确配置
2. **网络连接**：某些API可能需要代理或VPN
3. **配额限制**：检查API使用配额是否已用完
4. **Base URL**：确保各提供商的Base URL配置正确

#### 🔴 前端无响应
1. **清除缓存**：刷新页面或清除浏览器缓存
2. **检查控制台**：打开浏览器开发者工具查看错误信息
3. **重启服务**：停止服务后重新启动

#### 🔴 代码生成质量差
1. **优化需求描述**：提供更详细和具体的需求描述
2. **选择合适模型**：不同模型擅长不同类型的代码生成
3. **调整评分权重**：在 `config.json` 中调整评分权重

### 调试模式

启动调试模式获取更多日志信息：

```bash
# 后端调试
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# 查看详细日志
tail -f logs/app.log  # 如果配置了日志文件
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. **Fork** 项目
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **创建Pull Request**

### 开发规范

- **代码风格**：遵循PEP8规范
- **提交信息**：使用清晰的提交信息
- **测试覆盖**：添加必要的测试用例
- **文档更新**：更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目和服务：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Tailwind CSS](https://tailwindcss.com/) - 实用优先的CSS框架
- [OpenAI](https://openai.com/) - 提供强大的AI模型
- [Anthropic](https://anthropic.com/) - Claude AI模型
- [Google AI](https://ai.google/) - Gemini模型

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star！⭐**

[🐛 报告Bug](../../issues) · [✨ 功能建议](../../issues) · [📖 文档](../../wiki)

</div>