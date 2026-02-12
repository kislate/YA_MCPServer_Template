这个 modules 文件夹包含两个主要的工具模块：

---

## **1. YA_Secrets - 密钥管理模块**

**作用**：管理加密的敏感信息（API密钥、数据库密码等）

**使用方法**：

```python
from modules.YA_Secrets.secrets_parser import load_secrets, get_secret

# 加载所有密钥（返回字典）
all_secrets = load_secrets()  # 从 env.yaml 读取

# 获取单个密钥
api_key = get_secret('api_key')
db_password = get_secret('database_password')
```

**管理密钥数据**：运行脚本编辑加密文件
- Windows: windows.manage.ps1
- Linux/macOS: `source ./modules/YA_Secrets/linux-macos.manage.sh`

---

## **2. YA_Common - 通用工具模块**

### **日志工具** (logger.py)

```python
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("my_module")
logger.info("信息日志")
logger.error("错误日志")
logger.warning("警告日志")
```

### **配置管理** (config.py)

```python
from modules.YA_Common.utils.config import get_config, get_server_name

# 读取 config.yaml 中的配置（支持层级访问）
value = get_config('server.name')
custom_value = get_config('my.custom.setting', default='默认值')

# 快捷方法
name = get_server_name()
```

---

**总结**：
- **YA_Secrets**：加载 env.yaml 中的加密密钥
- **YA_Common**：提供日志记录、配置读取等通用功能