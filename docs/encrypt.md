Read [](file:///d%3A/Syncthing%20Folder/Asus-Lenovo/School%20Projects/project_agent/YA_MCPServer_Template/.sops.yaml)

Read [](file:///d%3A/Syncthing%20Folder/Asus-Lenovo/School%20Projects/project_agent/YA_MCPServer_Template/modules/YA_Secrets/windows.manage.ps1#1-1), lines 1 to 40

## 将你的 API 密钥添加到项目的完整步骤：

### **步骤 1：生成你的 age 密钥**（首次使用必需）

打开 PowerShell，在项目根目录运行：

```powershell
.\modules\YA_Secrets\windows.generate-age-key.ps1
```

这会生成密钥对并显示你的**公钥**（类似 `age1xxx...`）

### **步骤 2：配置 .sops.yaml**

将你的公钥添加到 .sops.yaml（在管理员公钥后面加逗号分隔）：

```yaml
creation_rules:
  - age: >-
      age13r4554wpmkkmh6lk2ky9d68nj7ctfgqv9d4f4ndu66h9usnxjfwsdcqvr7,
      你生成的公钥_age1xxxxx
```

### **步骤 3：添加 API 密钥**

运行管理脚本：

```powershell
.\modules\YA_Secrets\windows.manage.ps1
```

会自动打开编辑器，编辑成：

```yaml
secrets:
  api_key: sk-xxxxxxxxxxxxxx  # 你的实际 API 密钥
  my_custom_api: your_api_token_here  # 可以添加多个
```

保存并关闭编辑器，脚本会自动加密保存到 env.yaml

### **步骤 4：在代码中使用**

```python
from modules.YA_Secrets.secrets_parser import get_secret

# 获取你的 API 密钥
my_api_key = get_secret('api_key')
custom_api = get_secret('my_custom_api')

# 使用密钥调用 API
# requests.get('https://api.example.com', headers={'Authorization': f'Bearer {my_api_key}'})
```

---

**完成！** 你的 API 密钥现在已加密存储，代码可以安全读取使用。