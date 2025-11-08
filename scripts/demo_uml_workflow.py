"""
UML图表驱动代码生成 - 演示脚本

这个脚本演示了如何使用UML图表驱动的方式生成高质量代码
"""

import json
from datetime import datetime

# 演示数据：用户登录功能
DEMO_DATA = {
    "detailed_requirement": """
触发场景: 用户在登录页面输入用户名和密码
错误表现:
  - 错误日志: AuthenticationError: Invalid credentials
  - 功能影响: 用户无法登录系统
影响范围: 整个系统的用户认证功能
""",
    
    "architecture_design": """
技术栈: Python 3.9 + Flask + SQLAlchemy + bcrypt
架构模式: MVC三层架构
核心模块:
  - AuthController: 处理HTTP请求
  - UserService: 业务逻辑处理
  - UserRepository: 数据访问层
  - Database: 数据库连接管理
性能要求: 支持1000并发登录，响应时间<100ms
安全要求: 密码必须哈希存储，支持会话管理
""",
    
    "detailed_design": """
错误原因分析: 密码明文比对，未使用哈希验证
解决思路: 使用bcrypt进行密码哈希和验证

修正前代码:
def login(username, password):
    user = db.query(username)
    return user.password == password  # ❌ 明文比对

修正后代码:
def login(username, password):
    user = user_repo.find_by_username(username)
    if not user:
        raise AuthError("用户不存在")
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise AuthError("密码错误")
    return create_session(user)  # ✓ 哈希验证

关键步骤:
1. 使用Repository模式隔离数据访问
2. 使用bcrypt进行密码验证
3. 创建会话管理机制
4. 完善异常处理
""",
    
    "usecase_diagram": """
graph TD
    A[用户] -->|输入凭据| B(登录系统)
    B --> C{验证用户名}
    C -->|不存在| D[返回错误: 用户不存在]
    C -->|存在| E{验证密码}
    E -->|错误| F[返回错误: 密码错误]
    E -->|正确| G[创建会话]
    G --> H[跳转首页]
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style G fill:#e1ffe1
""",
    
    "component_diagram": """
graph TB
    subgraph "表示层"
        Controller[AuthController]
        Route[路由处理]
    end
    
    subgraph "业务层"
        Service[UserService]
        Auth[认证逻辑]
    end
    
    subgraph "数据层"
        Repo[UserRepository]
        DB[(数据库)]
    end
    
    Route --> Controller
    Controller --> Service
    Service --> Auth
    Auth --> Repo
    Repo --> DB
    
    style Controller fill:#e1f5ff
    style Service fill:#fff4e1
    style DB fill:#ffe1e1
""",
    
    "class_diagram": """
classDiagram
    class AuthController {
        +UserService service
        +login(username, password) dict
        +logout(session_id) dict
        +register(username, password) dict
    }
    
    class UserService {
        +UserRepository repo
        +authenticate(username, password) User
        +create_session(user) dict
        +hash_password(password) str
        +verify_password(password, hash) bool
    }
    
    class UserRepository {
        +Database db
        +find_by_username(username) User
        +find_by_id(user_id) User
        +save(user) None
        +update(user) None
    }
    
    class User {
        +int id
        +str username
        +str email
        +str password_hash
        +datetime created_at
    }
    
    class Database {
        +Connection conn
        +query(sql) Result
        +execute(sql) None
        +commit() None
    }
    
    AuthController --> UserService
    UserService --> UserRepository
    UserRepository --> Database
    UserRepository ..> User
    UserService ..> User
"""
}


# 期望生成的代码示例
EXPECTED_CODE = """
from typing import Optional
import bcrypt
from datetime import datetime

class User:
    def __init__(self, id: int, username: str, email: str, password_hash: str):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = datetime.now()

class Database:
    # 数据库连接管理类
    pass

class UserRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def find_by_username(self, username: str) -> Optional[User]:
        # 实现查询逻辑
        pass
    
    def save(self, user: User) -> None:
        # 实现保存逻辑
        pass

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
    
    def authenticate(self, username: str, password: str) -> User:
        user = self.repo.find_by_username(username)
        if not user:
            raise AuthError("用户不存在")
        if not self.verify_password(password, user.password_hash):
            raise AuthError("密码错误")
        return user
    
    def verify_password(self, password: str, hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), hash.encode())
    
    def create_session(self, user: User) -> dict:
        return {
            'user_id': user.id,
            'username': user.username,
            'created_at': datetime.now().isoformat()
        }

class AuthController:
    def __init__(self, service: UserService):
        self.service = service
    
    def login(self, username: str, password: str) -> dict:
        try:
            user = self.service.authenticate(username, password)
            session = self.service.create_session(user)
            return {'success': True, 'session': session}
        except AuthError as e:
            return {'success': False, 'error': str(e)}
"""


def print_demo_workflow():
    """打印演示工作流程"""
    print("=" * 80)
    print("[UML] UML图表驱动代码生成 - 演示工作流")
    print("=" * 80)
    print()
    
    print("[1] 第一步：详细需求描述")
    print("-" * 80)
    print(DEMO_DATA['detailed_requirement'])
    print()
    
    print("[>] 生成的用例图（Mermaid代码）:")
    print("-" * 80)
    print(DEMO_DATA['usecase_diagram'])
    print()
    
    print("[2] 第二步：架构设计")
    print("-" * 80)
    print(DEMO_DATA['architecture_design'])
    print()
    
    print("[>] 生成的组件图（Mermaid代码）:")
    print("-" * 80)
    print(DEMO_DATA['component_diagram'])
    print()
    
    print("[3] 第三步：详细设计")
    print("-" * 80)
    print(DEMO_DATA['detailed_design'])
    print()
    
    print("[>] 生成的类图（Mermaid代码）:")
    print("-" * 80)
    print(DEMO_DATA['class_diagram'])
    print()
    
    print("[4] 第四步：基于类图生成代码")
    print("-" * 80)
    print("期望生成的代码:")
    print(EXPECTED_CODE)
    print()
    
    print("=" * 80)
    print("[OK] 演示完成！")
    print("=" * 80)
    print()
    print("[!] 关键优势:")
    print("  1. 每一步都有图表验证，降低理解偏差")
    print("  2. 类图明确定义了所有接口，代码结构清晰")
    print("  3. 生成的代码包含完整实现，不是框架")
    print("  4. 自动添加类型注解和错误处理")
    print("  5. 代码质量显著提升！")
    print()


def save_demo_data_to_file():
    """保存演示数据到文件"""
    output_file = "demo_uml_data.json"
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "description": "UML图表驱动代码生成演示数据",
        "data": DEMO_DATA,
        "expected_code": EXPECTED_CODE
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[FILE] 演示数据已保存到: {output_file}")


if __name__ == "__main__":
    # 设置UTF-8编码（解决Windows控制台显示问题）
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print()
    print("=== Welcome to UML-Driven Code Generation Demo! ===")
    print()
    
    # 打印演示工作流
    print_demo_workflow()
    
    # 保存演示数据
    save_demo_data_to_file()
    
    print()
    print("[+] 如何使用:")
    print("  1. 启动Web服务: python web/start_server.py")
    print("  2. 打开浏览器: http://localhost:5000")
    print("  3. 复制上述内容到对应模块")
    print("  4. 点击'生成XXX图'按钮")
    print("  5. 点击'基于图表生成代码'")
    print("  6. 查看高质量的生成代码！")
    print()
    print("[*] 享受UML驱动的高质量代码生成体验！")
    print()

