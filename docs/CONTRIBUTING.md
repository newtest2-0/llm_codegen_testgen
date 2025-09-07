# 贡献指南

感谢您对CodeForge项目的关注！我们欢迎任何形式的贡献。

## 🤝 如何贡献

### 报告Bug
1. 在GitHub Issues中搜索是否已有相同问题
2. 如果没有，创建新的Issue
3. 提供详细的问题描述、复现步骤和环境信息

### 建议新功能
1. 在GitHub Issues中创建Feature Request
2. 详细描述功能需求和使用场景
3. 讨论实现方案

### 提交代码
1. Fork项目到你的GitHub账户
2. 创建特性分支：`git checkout -b feature/your-feature-name`
3. 进行开发并测试
4. 提交代码：`git commit -m "Add: your feature description"`
5. 推送到你的分支：`git push origin feature/your-feature-name`
6. 创建Pull Request

## 📝 开发规范

### 代码风格
- Python代码遵循PEP8规范
- JavaScript代码使用2空格缩进
- 使用有意义的变量和函数名
- 添加必要的注释

### 提交信息规范
使用以下格式的提交信息：
```
类型: 简短描述

详细描述（可选）
```

类型包括：
- `Add`: 新增功能
- `Fix`: 修复Bug
- `Update`: 更新功能
- `Remove`: 删除功能
- `Refactor`: 重构代码
- `Docs`: 文档更新
- `Style`: 代码格式调整
- `Test`: 测试相关

### 测试要求
- 新功能需要添加相应的测试用例
- 确保所有测试通过
- 测试覆盖率不低于80%

## 🏗️ 开发环境设置

### 1. 环境准备
```bash
# 克隆你的Fork
git clone https://github.com/your-username/llm_codegen_testgen.git
cd llm_codegen_testgen

# 添加上游仓库
git remote add upstream https://github.com/original-owner/llm_codegen_testgen.git

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 开发配置
```bash
# 复制环境变量文件
cp .env.example .env

# 配置API密钥（至少一个）
# 编辑.env文件
```

### 3. 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_specific.py

# 生成覆盖率报告
pytest --cov=backend --cov-report=html
```

### 4. 启动开发服务
```bash
# 启动开发服务
python scripts/start.py

# 或分别启动
cd backend && uvicorn app:app --reload
cd web && python start_server.py
```

## 📁 项目结构

```
llm_codegen_testgen/
├── backend/           # 后端代码
│   ├── api/          # API路由
│   ├── core/         # 核心模块
│   ├── models/       # 数据模型
│   └── services/     # 业务逻辑
├── web/              # 前端代码
├── tests/            # 测试文件
├── scripts/          # 工具脚本
└── docs/             # 文档
```

## 🔍 代码审查

所有Pull Request都会经过代码审查：

### 审查要点
- 代码质量和风格
- 功能完整性
- 测试覆盖率
- 文档更新
- 性能影响

### 审查流程
1. 自动化测试通过
2. 代码审查通过
3. 文档更新完成
4. 合并到主分支

## 🆘 获得帮助

如果在贡献过程中遇到问题：

1. 查看项目文档和README
2. 在GitHub Issues中搜索相关问题
3. 创建Discussion讨论技术问题
4. 联系项目维护者

## 📜 行为准则

参与本项目即表示您同意遵守我们的行为准则：

- 尊重所有参与者
- 友善和包容的交流
- 专注于对项目有益的建设性反馈
- 避免人身攻击和不当言论

## 🙏 致谢

感谢所有为项目做出贡献的开发者！

您的贡献将被记录在项目的贡献者列表中。
