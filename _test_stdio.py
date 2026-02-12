"""STDIO 工具调用完整测试"""
import subprocess, json, sys, time, threading

proc = subprocess.Popen(
    [sys.executable, "server.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, bufsize=1, encoding="utf-8", errors="replace"
)

def send(msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()

def recv(timeout=60):
    """读取一行 stdout，带超时"""
    result = [None]
    def _read():
        result[0] = proc.stdout.readline()
    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if result[0]:
        return json.loads(result[0])
    return None

# 后台读stderr
def read_stderr():
    while True:
        line = proc.stderr.readline()
        if not line:
            break
        print(f"  [SERVER] {line.rstrip()}")
threading.Thread(target=read_stderr, daemon=True).start()

# 1. Initialize
print(">>> Sending initialize...")
send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2024-11-05", "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0"}
}})
r = recv(15)
if r:
    print(f"<<< Init OK: {r['result']['serverInfo']['name']}")
else:
    print("<<< Init FAILED (timeout)")
    proc.terminate()
    sys.exit(1)

# 2. Initialized notification
send({"jsonrpc": "2.0", "method": "notifications/initialized"})
time.sleep(0.5)

# 3. 测试 add_knowledge（不填 title/tags/source，测试 AI 自动生成）
test_content = """# Python 装饰器详解

装饰器是 Python 的高级特性之一，允许在不修改函数源代码的情况下增强函数功能。

## 基本语法

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("调用前")
        result = func(*args, **kwargs)
        print("调用后")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")
```

## 常用装饰器
- @property: 属性装饰器
- @staticmethod: 静态方法
- @classmethod: 类方法
"""

print("\n>>> Calling add_knowledge (no title/tags/source, AI auto-generate)...")
start = time.time()
send({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
    "name": "add_knowledge", "arguments": {"content": test_content}
}})
r = recv(60)
elapsed = time.time() - start
if r:
    content = json.dumps(r, ensure_ascii=False, indent=2)[:800]
    print(f"<<< add_knowledge OK ({elapsed:.1f}s):\n{content}")
else:
    print(f"<<< add_knowledge TIMEOUT after {elapsed:.1f}s")

# 4. 测试 search_knowledge
print("\n>>> Calling search_knowledge...")
start = time.time()
send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
    "name": "search_knowledge", "arguments": {"query": "装饰器怎么用"}
}})
r = recv(30)
elapsed = time.time() - start
if r:
    content = json.dumps(r, ensure_ascii=False, indent=2)[:800]
    print(f"<<< search_knowledge OK ({elapsed:.1f}s):\n{content}")
else:
    print(f"<<< search_knowledge TIMEOUT after {elapsed:.1f}s")

# 5. 检查 raw 文件
print("\n>>> Checking raw markdown files...")
import os
raw_dir = "./data/raw"
if os.path.exists(raw_dir):
    files = os.listdir(raw_dir)
    print(f"  Found {len(files)} raw file(s): {files}")
    if files:
        with open(os.path.join(raw_dir, files[0]), "r", encoding="utf-8") as f:
            head = f.read(300)
        print(f"  First file content (head):\n{head}")
else:
    print("  No raw directory found!")

print("\n=== Test complete ===")
proc.terminate()
