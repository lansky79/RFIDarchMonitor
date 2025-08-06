# 设计文档

## 概述

档案库房智能监测系统采用简单的 B/S 架构，使用 Python Flask 作为后端服务，原生 HTML/CSS/JavaScript 作为前端界面。系统设计遵循简单易调试、快速开发的原则，所有数据持久化存储在 SQLite 数据库中。

## 架构设计

### 整体架构

```
┌─────────────────┐    HTTP API    ┌─────────────────┐    Serial/USB    ┌─────────────────┐
│   前端界面      │ ◄──────────── │   Flask后端     │ ◄──────────────► │   硬件设备      │
│  (HTML/CSS/JS)  │                │   (Python)      │                  │ (RFID/传感器)   │
└─────────────────┘                └─────────────────┘                  └─────────────────┘
                                           │
                                           ▼
                                   ┌─────────────────┐
                                   │   SQLite数据库  │
                                   │   (持久化存储)  │
                                   └─────────────────┘
```

### 技术栈选择

**前端技术：**

- HTML5 + CSS3 + 原生 JavaScript
- Bootstrap 5 (CSS 框架，提供基础样式)
- Chart.js (图表展示)
- 无需编译打包，直接在浏览器运行

**后端技术：**

- Python 3.8+
- Flask (轻量级 Web 框架)
- SQLite (嵌入式数据库)
- pyserial (串口通信)
- APScheduler (定时任务)

**开发调试：**

- 前端：修改文件后刷新浏览器即可
- 后端：修改代码后重启 Flask 服务即可
- 数据库：使用 SQLite Browser 可视化管理

## 组件和接口

### 前端组件结构

```
frontend/
├── index.html              # 主页面
├── css/
│   ├── bootstrap.min.css   # Bootstrap样式
│   └── custom.css          # 自定义样式
├── js/
│   ├── bootstrap.min.js    # Bootstrap脚本
│   ├── chart.min.js        # 图表库
│   ├── api.js              # API调用封装
│   └── main.js             # 主要业务逻辑
└── pages/
    ├── environment.html    # 环境监测页面
    ├── rfid.html          # RFID设备管理页面
    ├── tracking.html      # 档案追踪页面
    ├── inventory.html     # 盘点系统页面
    ├── alerts.html        # 告警管理页面
    ├── reports.html       # 统计报表页面
    ├── maintenance.html   # 设备维护页面
    └── settings.html      # 系统配置页面
```

### 后端组件结构

```
backend/
├── app.py                 # Flask应用主文件
├── config.py              # 配置管理
├── database.py            # 数据库连接和初始化
├── models/
│   ├── __init__.py
│   ├── environment.py     # 环境数据模型
│   ├── rfid.py           # RFID设备和标签模型
│   ├── archive.py        # 档案信息模型
│   ├── alert.py          # 告警信息模型
│   └── maintenance.py    # 维护记录模型
├── services/
│   ├── __init__.py
│   ├── environment_service.py    # 环境监测服务
│   ├── rfid_service.py          # RFID设备服务
│   ├── tracking_service.py      # 档案追踪服务
│   ├── inventory_service.py     # 盘点服务
│   ├── alert_service.py         # 告警服务
│   └── hardware_service.py     # 硬件通信服务
└── api/
    ├── __init__.py
    ├── environment_api.py        # 环境监测API
    ├── rfid_api.py              # RFID管理API
    ├── tracking_api.py          # 档案追踪API
    ├── inventory_api.py         # 盘点系统API
    ├── alert_api.py             # 告警管理API
    ├── report_api.py            # 统计报表API
    ├── maintenance_api.py       # 设备维护API
    └── settings_api.py          # 系统配置API
```

### API 接口设计

**环境监测 API：**

- GET /api/environment/data - 获取环境数据
- GET /api/environment/history - 获取历史数据
- POST /api/environment/thresholds - 设置告警阈值

**RFID 设备管理 API：**

- GET /api/rfid/devices - 获取设备列表
- POST /api/rfid/devices - 添加设备
- PUT /api/rfid/devices/{id} - 更新设备配置
- GET /api/rfid/tags - 获取标签列表
- POST /api/rfid/tags - 添加标签

**档案追踪 API：**

- GET /api/tracking/archives - 获取档案列表
- GET /api/tracking/location/{archive_id} - 获取档案位置
- GET /api/tracking/history/{archive_id} - 获取移动历史

**盘点系统 API：**

- POST /api/inventory/start - 开始盘点任务
- GET /api/inventory/status - 获取盘点状态
- GET /api/inventory/report - 获取盘点报告

**告警管理 API：**

- GET /api/alerts - 获取告警列表
- PUT /api/alerts/{id}/handle - 处理告警
- POST /api/alerts/rules - 设置告警规则

## 数据模型

### 数据库表设计

**环境数据表 (environment_data)：**

```sql
CREATE TABLE environment_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT NOT NULL,
    temperature REAL,
    humidity REAL,
    light_intensity REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    location TEXT
);
```

**RFID 设备表 (rfid_devices)：**

```sql
CREATE TABLE rfid_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT NOT NULL,
    device_type TEXT NOT NULL,
    serial_port TEXT,
    ip_address TEXT,
    status TEXT DEFAULT 'offline',
    config_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**RFID 标签表 (rfid_tags)：**

```sql
CREATE TABLE rfid_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_id TEXT UNIQUE NOT NULL,
    archive_id TEXT,
    tag_type TEXT,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**档案信息表 (archives)：**

```sql
CREATE TABLE archives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archive_code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    description TEXT,
    rfid_tag_id TEXT,
    current_location TEXT,
    status TEXT DEFAULT 'normal',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**位置记录表 (location_history)：**

```sql
CREATE TABLE location_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archive_id INTEGER,
    rfid_device_id INTEGER,
    location TEXT NOT NULL,
    action_type TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (archive_id) REFERENCES archives (id),
    FOREIGN KEY (rfid_device_id) REFERENCES rfid_devices (id)
);
```

**告警记录表 (alerts)：**

```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    level TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    source_id TEXT,
    status TEXT DEFAULT 'pending',
    handled_by TEXT,
    handled_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**盘点任务表 (inventory_tasks)：**

```sql
CREATE TABLE inventory_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    area TEXT,
    status TEXT DEFAULT 'pending',
    total_expected INTEGER DEFAULT 0,
    total_found INTEGER DEFAULT 0,
    missing_count INTEGER DEFAULT 0,
    extra_count INTEGER DEFAULT 0,
    started_at DATETIME,
    completed_at DATETIME,
    created_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**设备维护记录表 (maintenance_records)：**

```sql
CREATE TABLE maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_type TEXT NOT NULL,
    device_id INTEGER,
    maintenance_type TEXT NOT NULL,
    description TEXT,
    cost REAL,
    technician TEXT,
    scheduled_date DATETIME,
    completed_date DATETIME,
    status TEXT DEFAULT 'scheduled',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**系统配置表 (system_config)：**

```sql
CREATE TABLE system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    config_type TEXT DEFAULT 'string',
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 错误处理

### 错误分类

**系统错误：**

- 数据库连接错误
- 硬件设备通信错误
- 文件读写错误

**业务错误：**

- 数据验证错误
- 权限不足错误
- 资源不存在错误

**硬件错误：**

- 传感器读取失败
- RFID 设备连接失败
- 串口通信超时

### 错误处理策略

**前端错误处理：**

```javascript
// API调用错误处理
async function apiCall(url, options) {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("API调用失败:", error);
    showErrorMessage(error.message);
    return null;
  }
}
```

**后端错误处理：**

```python
# Flask错误处理装饰器
from functools import wraps
import logging

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logging.warning(f"验证错误: {e}")
            return {"error": str(e), "code": 400}, 400
        except DatabaseError as e:
            logging.error(f"数据库错误: {e}")
            return {"error": "数据库操作失败", "code": 500}, 500
        except HardwareError as e:
            logging.error(f"硬件错误: {e}")
            return {"error": "硬件设备通信失败", "code": 503}, 503
        except Exception as e:
            logging.error(f"未知错误: {e}")
            return {"error": "系统内部错误", "code": 500}, 500
    return decorated_function
```

## 测试策略

### 单元测试

**后端测试：**

- 使用 pytest 进行单元测试
- 测试数据库操作
- 测试 API 接口
- 测试业务逻辑

**前端测试：**

- 使用浏览器开发者工具进行调试
- 手动测试用户界面交互
- 测试 API 调用和数据展示

### 集成测试

**硬件集成测试：**

- 模拟传感器数据输入
- 测试 RFID 设备通信
- 测试数据采集和存储流程

**系统集成测试：**

- 端到端功能测试
- 用户场景测试
- 性能和稳定性测试

### 测试数据

**环境数据模拟：**

```python
# 生成测试环境数据
def generate_test_environment_data():
    return {
        "temperature": random.uniform(18.0, 25.0),
        "humidity": random.uniform(40.0, 60.0),
        "light_intensity": random.uniform(100.0, 500.0),
        "sensor_id": "SENSOR_001",
        "location": "档案室A区"
    }
```

**RFID 标签模拟：**

```python
# 生成测试RFID标签
def generate_test_rfid_tags():
    return [
        {"tag_id": "E200001", "archive_id": "ARCH001", "tag_type": "档案标签"},
        {"tag_id": "E200002", "archive_id": "ARCH002", "tag_type": "档案标签"},
        {"tag_id": "E200003", "archive_id": "ARCH003", "tag_type": "档案标签"}
    ]
```
