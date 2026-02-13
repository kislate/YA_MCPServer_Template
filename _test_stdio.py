"""STDIO 工具调用完整测试 - 记忆库 + 无匹配AI直接回答"""
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
    result = [None]
    def _read():
        result[0] = proc.stdout.readline()
    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if result[0]:
        return json.loads(result[0])
    return None

def read_stderr():
    while True:
        line = proc.stderr.readline()
        if not line:
            break
        print(f"  [SERVER] {line.rstrip()}")
threading.Thread(target=read_stderr, daemon=True).start()

# ── 1. Initialize ──
print(">>> [1] Initialize...")
send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2024-11-05", "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0"}
}})
r = recv(15)
if r:
    print(f"<<< OK: {r['result']['serverInfo']['name']}")
else:
    print("<<< FAILED"); proc.terminate(); sys.exit(1)
send({"jsonrpc": "2.0", "method": "notifications/initialized"})
time.sleep(0.5)

# ── 2. add_knowledge (Python 装饰器) ──
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
```
## 常用装饰器
- @property: 属性装饰器
- @staticmethod: 静态方法
"""

print("\n>>> [2] add_knowledge (装饰器)...")
start = time.time()
send({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
    "name": "add_knowledge", "arguments": {"content": test_content}
}})
r = recv(60)
elapsed = time.time() - start
if r:
    try:
        text = r["result"]["content"][0]["text"]
        data = json.loads(text)
        print(f"<<< OK ({elapsed:.1f}s): id={data['id']}, title={data['title']}")
    except Exception:
        print(f"<<< OK ({elapsed:.1f}s): {json.dumps(r, ensure_ascii=False)[:300]}")
else:
    print(f"<<< TIMEOUT ({elapsed:.1f}s)")

# ── 3. search_knowledge (相关查询 → 应有结果) ──
print("\n>>> [3] search_knowledge('装饰器怎么用') → should have results...")
start = time.time()
send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
    "name": "search_knowledge", "arguments": {"query": "装饰器怎么用"}
}})
r = recv(30)
elapsed = time.time() - start
if r:
    try:
        text = r["result"]["content"][0]["text"]
        data = json.loads(text)
        n = data["total_results"]
        rels = [f"{x['relevance']:.3f}" for x in data["results"]]
        print(f"<<< OK ({elapsed:.1f}s): {n} results, relevances={rels}")
    except Exception:
        print(f"<<< OK ({elapsed:.1f}s): {json.dumps(r, ensure_ascii=False)[:400]}")
else:
    print(f"<<< TIMEOUT ({elapsed:.1f}s)")

# ── 4. search_knowledge (不相关查询 → 应该 0 结果) ──
print("\n>>> [4] search_knowledge('量化交易如何实现') → should be EMPTY...")
start = time.time()
send({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
    "name": "search_knowledge", "arguments": {"query": "量化交易如何实现"}
}})
r = recv(30)
elapsed = time.time() - start
if r:
    try:
        text = r["result"]["content"][0]["text"]
        data = json.loads(text)
        n = data["total_results"]
        print(f"<<< OK ({elapsed:.1f}s): {n} results {'✅ CORRECT (0)' if n == 0 else '❌ WRONG (should be 0)'}")
    except Exception:
        print(f"<<< OK ({elapsed:.1f}s): {json.dumps(r, ensure_ascii=False)[:400]}")
else:
    print(f"<<< TIMEOUT ({elapsed:.1f}s)")

# ── 5. ask_knowledge (不相关 → AI 直接回答模式) ──
print("\n>>> [5] ask_knowledge('量化交易如何实现') → should be AI direct mode...")
start = time.time()
send({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {
    "name": "ask_knowledge", "arguments": {"question": "量化交易如何实现"}
}})
r = recv(60)
elapsed = time.time() - start
if r:
    try:
        text = r["result"]["content"][0]["text"]
        data = json.loads(text)
        mode = data.get("mode", "?")
        answer_preview = data["answer"][:150]
        sources_count = len(data.get("sources", []))
        print(f"<<< OK ({elapsed:.1f}s): mode={mode} {'✅' if mode=='ai_direct' else '❌'}")
        print(f"    sources={sources_count} (should be 0)")
        print(f"    answer={answer_preview}...")
    except Exception:
        print(f"<<< OK ({elapsed:.1f}s): {json.dumps(r, ensure_ascii=False)[:500]}")
else:
    print(f"<<< TIMEOUT ({elapsed:.1f}s)")

# 等待后处理
print("\n  Waiting 12s for async post-processing...")
time.sleep(12)

# ── 6. memory_stats (应该有记忆 + 画像) ──
print("\n>>> [6] memory_stats...")
send({"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {
    "name": "memory_stats", "arguments": {}
}})
r = recv(10)
if r:
    try:
        text = r["result"]["content"][0]["text"]
        data = json.loads(text)
        total = data["total_memories"]
        profile = data.get("user_profile", {})
        print(f"<<< OK: memories={total}, interests={profile.get('interests', [])}, level={profile.get('level', '')}")
    except Exception:
        print(f"<<< OK: {json.dumps(r, ensure_ascii=False)[:400]}")
else:
    print("<<< TIMEOUT")

# ── 7. ask_knowledge (相关 → RAG 模式) ──
print("\n>>> [7] ask_knowledge('装饰器有什么用') → should be RAG mode...")
start = time.time()
send({"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {
    "name": "ask_knowledge", "arguments": {"question": "装饰器有什么用"}
}})
r = recv(60)
elapsed = time.time() - start
if r:
    try:
        text = r["result"]["content"][0]["text"]
        data = json.loads(text)
        mode = data.get("mode", "?")
        sources_count = len(data.get("sources", []))
        mem_count = len(data.get("memory_sources", []))
        print(f"<<< OK ({elapsed:.1f}s): mode={mode} {'✅' if mode=='rag' else '❌'}, sources={sources_count}, memory_sources={mem_count}")
    except Exception:
        print(f"<<< OK ({elapsed:.1f}s): {json.dumps(r, ensure_ascii=False)[:500]}")
else:
    print(f"<<< TIMEOUT ({elapsed:.1f}s)")

# ── 8. 检查用户画像文件 ──
print("\n>>> [8] Checking user_profile.json...")
import os
profile_path = "./data/memory/user_profile.json"
if os.path.exists(profile_path):
    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    print(f"  ✅ Profile: interests={profile.get('interests', [])}, level={profile.get('level', '')}")
    print(f"     topics={profile.get('frequent_topics', {})}")
else:
    print("  ❌ No user_profile.json found")

print("\n=== ALL TESTS COMPLETE ===")
proc.terminate()
