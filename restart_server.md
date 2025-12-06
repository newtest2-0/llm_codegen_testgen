# 重启服务器步骤

## 1. 停止当前服务器
在运行 `python start.py` 的终端窗口中：
- 按 `Ctrl + C` 停止服务器

## 2. 启动服务器
```bash
python start.py
```

## 3. 验证路由已加载
启动时应该看到类似的日志：
```
🚀 启动LLM代码生成平台...
✅ 已加载 X 个AI提供者
```

## 4. 清空浏览器缓存
- 访问 http://localhost:8080
- 按 `Ctrl + Shift + R` (强制刷新)
- 或 `Ctrl + F5`

## 5. 测试LLM评阅
1. 滚动到 "Professional需求管理" 区域
2. 在"详细需求描述"框输入测试内容
3. 点击 "🤖 LLMs评阅" 按钮
4. 应该看到评阅结果，不再出现404错误

## 预期日志
```
POST /api/v1/requirements/documents/xxx/llm-review HTTP/1.1" 200 OK
```

不应该再看到 404 Not Found！
