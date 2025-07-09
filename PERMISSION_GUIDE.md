# 权限管理系统使用指南

## 概述

本系统实现了基于角色和权限的访问控制（RBAC）系统，支持细粒度的权限管理和灵活的权限检查。

## 系统架构

### 核心组件

1. **权限模型** (`modules/tornadoapp/model/permission_model.py`)
   - `Role`: 角色模型
   - `Permission`: 权限模型
   - `UserRole`: 用户角色关联模型
   - `PermissionGroup`: 权限组模型

2. **权限工具** (`modules/tornadoapp/utils/permission_utils.py`)
   - `PermissionUtils`: 权限管理工具类

3. **权限装饰器** (`modules/tornadoapp/utils/permission_decorator.py`)
   - 各种权限检查装饰器
   - `PermissionMixin`: 权限混入类

4. **权限处理器** (`modules/tornadoapp/handler/permission_handler.py`)
   - 角色管理API
   - 权限管理API
   - 用户角色管理API

## 权限系统初始化

### 1. 运行初始化脚本

```bash
cd modules/tornadoapp/utils
python init_permissions.py
```

### 2. 初始化内容

- **系统权限**: 用户、角色、权限、系统、数据管理权限
- **系统角色**: super_admin、admin、user_manager、data_manager、user、guest
- **权限组**: 按功能模块分组的权限集合

## 权限装饰器使用

### 1. 单个权限检查

```python
from modules.tornadoapp.utils.permission_decorator import require_permission

class MyHandler(RequestHandler):
    @require_permission("data:read")
    async def get(self):
        # 需要data:read权限才能访问
        pass
```

### 2. 多个权限检查

```python
from modules.tornadoapp.utils.permission_decorator import require_permissions

class MyHandler(RequestHandler):
    @require_permissions(["user:read", "user:write"], require_all=True)
    async def post(self):
        # 需要同时拥有user:read和user:write权限
        pass
    
    @require_permissions(["user:read", "user:admin"], require_all=False)
    async def get(self):
        # 需要user:read或user:admin权限之一
        pass
```

### 3. 管理员权限检查

```python
from modules.tornadoapp.utils.permission_decorator import require_admin

class MyHandler(RequestHandler):
    @require_admin()
    async def post(self):
        # 需要管理员权限
        pass
```

### 4. 角色检查

```python
from modules.tornadoapp.utils.permission_decorator import require_role, require_roles

class MyHandler(RequestHandler):
    @require_role("admin")
    async def get(self):
        # 需要admin角色
        pass
    
    @require_roles(["admin", "user_manager"], require_all=False)
    async def post(self):
        # 需要admin或user_manager角色之一
        pass
```

## 权限混入类使用

### 1. 继承PermissionMixin

```python
from modules.tornadoapp.utils.permission_decorator import PermissionMixin

class MyHandler(RequestHandler, PermissionMixin):
    async def get(self):
        # 获取当前用户ID
        user_id = await self.get_current_user_id()
        
        # 检查单个权限
        can_read = await self.check_permission("data:read")
        
        # 检查多个权限
        permissions = await self.check_permissions(["user:read", "role:read"])
        
        # 检查是否管理员
        is_admin = await self.is_admin()
        
        # 获取权限摘要
        summary = await self.get_user_permission_summary()
```

## API接口说明

### 角色管理

#### 获取角色列表
```
GET /api/roles?page=1&limit=10
```

#### 获取单个角色
```
GET /api/roles/{role_id}
```

#### 创建角色
```
POST /api/roles
Content-Type: application/json

{
    "name": "editor",
    "description": "编辑者角色",
    "permissions": ["data:read", "data:write"]
}
```

#### 更新角色
```
PUT /api/roles/{role_id}
Content-Type: application/json

{
    "name": "senior_editor",
    "description": "高级编辑者角色",
    "permissions": ["data:read", "data:write", "data:delete"]
}
```

#### 删除角色
```
DELETE /api/roles/{role_id}
```

### 权限管理

#### 获取权限列表
```
GET /api/permissions?page=1&limit=10
```

#### 创建权限
```
POST /api/permissions
Content-Type: application/json

{
    "name": "report:export",
    "resource": "report",
    "action": "export",
    "description": "导出报告权限"
}
```

### 用户角色管理

#### 获取用户角色
```
GET /api/users/{user_id}/roles
```

#### 为用户分配角色
```
POST /api/users/{user_id}/roles
Content-Type: application/json

{
    "role_id": "role_id_here",
    "expires_at": "2024-12-31T23:59:59Z"  // 可选
}
```

#### 移除用户角色
```
DELETE /api/users/{user_id}/roles/{role_id}
```

### 用户权限管理

#### 获取用户权限信息
```
GET /api/users/{user_id}/permissions
```

#### 检查用户权限
```
POST /api/users/{user_id}/permissions
Content-Type: application/json

{
    "permissions": ["data:read", "user:write"]
}
```

#### 获取当前用户权限
```
GET /api/permissions
```

## 业务处理器示例

### 数据管理处理器

```python
class DataHandler(RequestHandler, PermissionMixin):
    @require_permission("data:read")
    async def get(self, data_id=None):
        # 需要data:read权限
        pass
    
    @require_permission("data:write")
    async def post(self):
        # 需要data:write权限
        pass
    
    @require_permission("data:delete")
    async def delete(self, data_id):
        # 需要data:delete权限
        pass
```

### 系统管理处理器

```python
class SystemHandler(RequestHandler, PermissionMixin):
    @require_permission("system:read")
    async def get(self):
        # 需要system:read权限
        pass
    
    @require_admin()
    async def post(self):
        # 需要管理员权限
        pass
```

## 权限检查流程

1. **请求到达**: 客户端发送请求到服务器
2. **认证检查**: 中间件验证JWT token
3. **权限检查**: 装饰器检查用户权限
4. **业务处理**: 执行具体的业务逻辑
5. **响应返回**: 返回处理结果

## 权限命名规范

权限名称采用 `资源:操作` 的格式：

- `user:read` - 读取用户信息
- `user:write` - 创建/更新用户
- `user:delete` - 删除用户
- `user:admin` - 用户管理
- `role:read` - 读取角色信息
- `role:write` - 创建/更新角色
- `role:delete` - 删除角色
- `role:admin` - 角色管理
- `system:admin` - 系统管理
- `data:read` - 读取数据
- `data:write` - 创建/更新数据
- `data:delete` - 删除数据
- `data:admin` - 数据管理

## 最佳实践

### 1. 权限设计原则

- **最小权限原则**: 只授予必要的最小权限
- **职责分离**: 不同角色承担不同职责
- **权限继承**: 通过角色继承权限，避免直接分配
- **定期审查**: 定期审查和更新权限配置

### 2. 代码组织

- 使用装饰器保护敏感接口
- 在业务逻辑中使用混入类进行动态权限检查
- 保持权限检查的一致性和可维护性

### 3. 安全考虑

- 所有敏感操作都需要权限验证
- 使用HTTPS传输
- 定期轮换JWT密钥
- 记录权限相关的审计日志

## 故障排除

### 常见问题

1. **权限检查失败**
   - 检查用户是否已登录
   - 确认用户角色是否正确分配
   - 验证权限名称是否正确

2. **角色分配失败**
   - 确认角色是否存在且激活
   - 检查分配者是否有相应权限
   - 验证用户ID和角色ID格式

3. **初始化失败**
   - 确认数据库连接正常
   - 检查MongoDB服务状态
   - 验证环境变量配置

### 调试技巧

1. 使用权限摘要接口查看用户权限
2. 检查MongoDB中的权限数据
3. 查看应用日志了解权限检查过程
4. 使用Postman等工具测试API接口 