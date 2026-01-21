# 定时任务管理API使用文档

## 概述

定时任务管理API提供了完整的定时任务管理功能，包括创建、查询、更新、删除、暂停、恢复和立即触发等操作。

## API端点

### 1. 获取任务列表

**GET** `/api/scheduler/jobs`

**查询参数：**
- `page` (int, 可选): 页码，默认1
- `limit` (int, 可选): 每页数量，默认20
- `status` (string, 可选): 状态过滤 (active/paused/removed)
- `is_active` (bool, 可选): 是否激活过滤

**响应示例：**
```json
{
  "jobs": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "数据下载任务",
      "job_id": "download_data",
      "func_path": "utils.data:download_all_data",
      "trigger_type": "cron",
      "status": "active",
      "is_active": true,
      "args": [],
      "kwargs": {},
      "trigger": {
        "day_of_week": "0-4",
        "hour": 15,
        "minute": 40,
        "second": 0
      },
      "next_run_time": "2024-01-15T15:40:00",
      "last_run_time": "2024-01-14T15:40:00",
      "run_count": 10,
      "error_count": 0,
      "description": "每周一至周五15:40执行数据下载"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "pages": 1
  }
}
```

### 2. 获取单个任务详情

**GET** `/api/scheduler/jobs/{job_id}`

**响应示例：**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "数据下载任务",
  "job_id": "download_data",
  "func_path": "utils.data:download_all_data",
  "trigger_type": "cron",
  "status": "active",
  "is_active": true,
  "args": [],
  "kwargs": {},
  "trigger": {
    "day_of_week": "0-4",
    "hour": 15,
    "minute": 40,
    "second": 0
  },
  "next_run_time": "2024-01-15T15:40:00",
  "last_run_time": "2024-01-14T15:40:00",
  "run_count": 10,
  "error_count": 0
}
```

### 3. 创建定时任务

**POST** `/api/scheduler/jobs`

**请求体（Cron触发器）：**
```json
{
  "name": "数据下载任务",
  "job_id": "download_data",
  "func_path": "utils.data:download_all_data",
  "trigger_type": "cron",
  "day_of_week": "0-4",
  "hour": 15,
  "minute": 40,
  "second": 0,
  "args": [],
  "kwargs": {},
  "description": "每周一至周五15:40执行数据下载"
}
```

**请求体（Interval触发器）：**
```json
{
  "name": "每分钟检查任务",
  "job_id": "check_task",
  "func_path": "utils.task:check_status",
  "trigger_type": "interval",
  "interval_minutes": 1,
  "args": ["param1"],
  "kwargs": {"key": "value"},
  "description": "每分钟执行一次检查"
}
```

**请求体（Date触发器）：**
```json
{
  "name": "单次执行任务",
  "job_id": "one_time_task",
  "func_path": "utils.task:one_time_job",
  "trigger_type": "date",
  "run_date": "2024-12-31T23:59:59",
  "args": [],
  "kwargs": {},
  "description": "在指定时间执行一次"
}
```

### 4. 更新定时任务

**PUT** `/api/scheduler/jobs/{job_id}`

**请求体：**
```json
{
  "name": "更新后的任务名称",
  "description": "更新后的描述",
  "hour": 16,
  "minute": 30,
  "args": ["new_param"],
  "kwargs": {"new_key": "new_value"}
}
```

### 5. 删除定时任务

**DELETE** `/api/scheduler/jobs/{job_id}`

**响应：**
```json
{
  "message": "任务已删除",
  "job_id": "download_data"
}
```

### 6. 暂停任务

**POST** `/api/scheduler/jobs/{job_id}/pause`

**响应：**
```json
{
  "message": "任务已暂停",
  "job_id": "download_data",
  "action": "pause"
}
```

### 7. 恢复任务

**POST** `/api/scheduler/jobs/{job_id}/resume`

**响应：**
```json
{
  "message": "任务已恢复",
  "job_id": "download_data",
  "action": "resume"
}
```

### 8. 立即触发任务

**POST** `/api/scheduler/jobs/{job_id}/trigger`

**响应：**
```json
{
  "message": "任务已触发",
  "job_id": "download_data",
  "action": "trigger"
}
```

### 9. 获取统计信息

**GET** `/api/scheduler/stats`

**响应：**
```json
{
  "total": 5,
  "active": 3,
  "paused": 1,
  "removed": 1,
  "by_trigger_type": {
    "cron": 3,
    "interval": 1,
    "date": 1
  },
  "execution_stats": {
    "total_runs": 100,
    "total_errors": 2,
    "error_rate": 0.02
  }
}
```

## 触发器类型说明

### Cron触发器

适用于按固定时间表执行的任务，如每天、每周、每月等。

**参数：**
- `day_of_week`: 星期几，格式：`"0-4"` (周一到周五), `"mon-fri"`, `"0,6"` (周末)
- `hour`: 小时 (0-23)
- `minute`: 分钟 (0-59)
- `second`: 秒 (0-59)，默认0

**示例：**
- 每天9:30执行：`{"hour": 9, "minute": 30}`
- 每周一到周五15:40执行：`{"day_of_week": "0-4", "hour": 15, "minute": 40}`
- 每小时执行：`{"minute": 0}`

### Interval触发器

适用于按固定间隔执行的任务。

**参数（至少指定一个）：**
- `interval_seconds`: 间隔秒数
- `interval_minutes`: 间隔分钟数
- `interval_hours`: 间隔小时数
- `interval_days`: 间隔天数

**示例：**
- 每5分钟执行：`{"interval_minutes": 5}`
- 每30秒执行：`{"interval_seconds": 30}`
- 每2小时执行：`{"interval_hours": 2}`

### Date触发器

适用于在指定时间执行一次的任务。

**参数：**
- `run_date`: 执行日期时间，ISO格式字符串

**示例：**
- `{"run_date": "2024-12-31T23:59:59"}`

## 函数路径格式

`func_path` 必须遵循格式：`module.path:function_name`

**示例：**
- `utils.data:download_all_data` - 调用 `utils.data` 模块的 `download_all_data` 函数
- `modules.tornadoapp.auto_trader:monitor_positions` - 调用 `modules.tornadoapp.auto_trader` 模块的 `monitor_positions` 函数

## 参数传递

### args (位置参数)

数组格式，按顺序传递给函数。

**示例：**
```json
{
  "args": ["param1", "param2", 123]
}
```

### kwargs (关键字参数)

对象格式，以键值对形式传递给函数。

**示例：**
```json
{
  "kwargs": {
    "key1": "value1",
    "key2": 123,
    "key3": true
  }
}
```

## 权限要求

所有API端点都需要相应的权限：
- 查询操作：`system:read`
- 创建/更新/删除操作：`system:write`

## 错误处理

所有API在出错时返回统一格式：

```json
{
  "code": "ERROR_CODE",
  "msg": "错误信息",
  "data": {}
}
```

常见错误：
- `缺少必填字段: {field}` - 缺少必填参数
- `任务ID已存在: {job_id}` - 任务ID重复
- `任务不存在` - 任务不存在
- `参数错误: {message}` - 参数格式错误
- `导入函数失败 {func_path}` - 无法导入指定函数

## 使用示例

### Python示例

```python
import requests

# 创建任务
response = requests.post(
    "http://localhost:8888/api/scheduler/jobs",
    json={
        "name": "数据下载任务",
        "job_id": "download_data",
        "func_path": "utils.data:download_all_data",
        "trigger_type": "cron",
        "day_of_week": "0-4",
        "hour": 15,
        "minute": 40,
        "args": [],
        "kwargs": {},
        "description": "每周一至周五15:40执行数据下载"
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

# 获取任务列表
response = requests.get(
    "http://localhost:8888/api/scheduler/jobs",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

# 暂停任务
response = requests.post(
    "http://localhost:8888/api/scheduler/jobs/download_data/pause",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### cURL示例

```bash
# 创建任务
curl -X POST http://localhost:8888/api/scheduler/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "数据下载任务",
    "job_id": "download_data",
    "func_path": "utils.data:download_all_data",
    "trigger_type": "cron",
    "day_of_week": "0-4",
    "hour": 15,
    "minute": 40,
    "description": "每周一至周五15:40执行数据下载"
  }'

# 获取任务列表
curl -X GET http://localhost:8888/api/scheduler/jobs \
  -H "Authorization: Bearer YOUR_TOKEN"

# 暂停任务
curl -X POST http://localhost:8888/api/scheduler/jobs/download_data/pause \
  -H "Authorization: Bearer YOUR_TOKEN"
```

