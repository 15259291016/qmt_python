# API迁移指南：从手动JSON解析到Pydantic自动生成

## 迁移目标

将现有API从手动JSON解析迁移到**类型注解 + Pydantic**方案，实现：
- ✅ 自动生成Swagger文档
- ✅ 自动参数验证
- ✅ 类型安全
- ✅ 代码简洁

---

## 迁移步骤

### 步骤1：创建Pydantic模型

在 `modules/tornadoapp/schemas/` 下创建对应的模型文件：

```python
# schemas/user_schemas.py
from pydantic import BaseModel, Field, EmailStr

class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
```

### 步骤2：更新Handler方法签名

**旧方式（手动解析）：**
```python
async def post(self):
    data = json.loads(self.request.body)
    username = data.get("username")
    # ... 手动验证和解析
```

**新方式（Pydantic自动解析）：**
```python
async def post(self) -> UserResponse:
    """创建用户 - 请求体自动解析为UserCreateRequest"""
    request = self.parse_pydantic_model(UserCreateRequest)
    # request.username, request.email 已自动验证
```

### 步骤3：使用类型注解

**查询参数（GET）：**
```python
async def get(
    self,
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None
) -> UserListResponse:
    # 参数自动从查询字符串解析，带类型转换
```

**路径参数：**
```python
async def put(self, user_id: str) -> UserResponse:
    # user_id 自动从路径提取
```

**请求体（POST/PUT）：**
```python
async def post(self) -> UserResponse:
    request = self.parse_pydantic_model(UserCreateRequest)
    # 自动验证和解析
```

### 步骤4：返回类型注解

```python
async def get(self) -> UserListResponse:
    # 返回Pydantic模型，自动序列化
    return UserListResponse(users=[...], pagination={...})
```

---

## 已迁移的API

### ✅ 定时任务API

**文件：** `modules/tornadoapp/controller/scheduler_handler_v2.py`

**模型：** `modules/tornadoapp/schemas/scheduler_schemas.py`

**示例：**
```python
class SchedulerJobHandler(BaseHandler, PermissionMixin):
    async def post(self) -> ScheduledJobResponse:
        """创建定时任务"""
        request = self.parse_pydantic_model(ScheduledJobCreateRequest)
        # ... 业务逻辑
        return ScheduledJobResponse(**job_info)
```

---

## 迁移检查清单

- [ ] 创建Pydantic请求模型（Request）
- [ ] 创建Pydantic响应模型（Response）
- [ ] 更新Handler方法签名（添加类型注解）
- [ ] 使用 `parse_pydantic_model()` 解析请求体
- [ ] 使用类型注解定义查询参数
- [ ] 返回Pydantic响应模型
- [ ] 测试API功能
- [ ] 验证Swagger文档自动生成

---

## 待迁移API列表

### 高优先级
- [ ] **用户管理API** (`user_handler.py`)
  - GET /api/users - 用户列表
  - POST /api/users - 创建用户
  - PUT /api/users/{id} - 更新用户
  - DELETE /api/users/{id} - 删除用户

- [ ] **持仓分析API** (`position_handler.py`)
  - GET /api/position/analysis - 持仓分析
  - POST /api/position/analysis - 提交持仓分析

### 中优先级
- [ ] **权限管理API** (`permission_handler.py`)
- [ ] **风险控制API** (`risk_api.py`)
- [ ] **合规管理API** (`compliance_api.py`)

### 低优先级
- [ ] **业务处理器** (`business_handler.py`)
- [ ] **数据管理API** (`data_service`)

---

## 迁移示例对比

### 示例1：创建用户

**旧方式：**
```python
async def post(self):
    data = json.loads(self.request.body)
    if not data.get("username") or not data.get("email"):
        return FailedResponse(msg="缺少必填字段")
    # ... 手动验证和创建
```

**新方式：**
```python
async def post(self) -> UserResponse:
    """创建用户"""
    request = self.parse_pydantic_model(UserCreateRequest)
    # request已自动验证，直接使用
    user = User(username=request.username, email=request.email, ...)
    return UserResponse(**user.dict())
```

### 示例2：查询列表

**旧方式：**
```python
async def get(self):
    page = int(self.get_argument("page", 1))
    limit = int(self.get_argument("limit", 10))
    search = self.get_argument("search", "")
    # ... 手动类型转换
```

**新方式：**
```python
async def get(
    self,
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None
) -> UserListResponse:
    # 参数自动解析和类型转换
    # ... 业务逻辑
    return UserListResponse(users=[...], pagination={...})
```

---

## 注意事项

1. **向后兼容**：迁移时保持API路径和响应格式不变
2. **错误处理**：Pydantic验证失败会自动抛出 `ValidationError`，需要捕获
3. **可选参数**：使用 `Optional[Type]` 或 `Field(None, ...)` 定义可选参数
4. **枚举类型**：使用 `Enum` 类型，Pydantic自动验证
5. **日期时间**：使用 `datetime` 或 `str`（ISO格式），Pydantic自动转换

---

## 下一步

1. 完成用户管理API迁移
2. 完成持仓分析API迁移
3. 更新Swagger自动生成逻辑，支持Pydantic模型
4. 删除旧的手动维护的Swagger文档代码

