import os, re, subprocess, sys

ROOT = r"C:/Users/lianxiang/WorkBuddy/2026-07-23-09-09-54"
PY = r"C:/Users/lianxiang/.workbuddy/binaries/python/versions/3.13.12/python.exe"
CRED = r"C:/Users/lianxiang/Desktop/cloudfR2密钥.txt"

raw = open(CRED, encoding="utf-8", errors="replace").read()
envs = {}

# 账户 ID：从端点 https://<id>.r2.cloudflarestorage.com 提取
m = re.search(r"https://([A-Za-z0-9]+)\.r2\.", raw)
if not m:
    m = re.search(r"使用此令牌对\s*([A-Za-z0-9]+)\s*API", raw)
if m:
    envs["R2_ACCOUNT_ID"] = m.group(1).strip()

# 存储桶名：标签行「存储桶名：」下一非空行
m = re.search(r"存储桶名[：:]\s*\n\s*([^\n]+)", raw)
if m:
    envs["R2_BUCKET"] = m.group(1).strip()

# 访问密钥 ID：标签「访问密钥 ID」下一非空行
m = re.search(r"访问密钥\s*ID\s*\n\s*([^\n]+)", raw, re.IGNORECASE)
if m:
    envs["R2_ACCESS_KEY"] = m.group(1).strip()

# 机密访问密钥：标签「机密访问密钥」下一非空行
m = re.search(r"机密访问密钥\s*\n\s*([^\n]+)", raw)
if m:
    envs["R2_SECRET_KEY"] = m.group(1).strip()

# 仅打印非敏感信息，绝不打印密钥值
print("R2_ACCOUNT_ID FOUND len=", len(envs.get("R2_ACCOUNT_ID", "")))
print("R2_BUCKET =", envs.get("R2_BUCKET", "MISSING"))
print("R2_ACCESS_KEY FOUND" if "R2_ACCESS_KEY" in envs else "R2_ACCESS_KEY MISSING")
print("R2_SECRET_KEY FOUND" if "R2_SECRET_KEY" in envs else "R2_SECRET_KEY MISSING")
if len(envs) < 4:
    print("缺少凭证，停止")
    sys.exit(1)

env = os.environ.copy()
env.update(envs)
r = subprocess.run(
    [PY, "scripts/upload_r2_req.py", "--only", "twitter", "--workers", "16"],
    cwd=ROOT, env=env, capture_output=True, text=True,
)
sys.stdout.write(r.stdout)
if r.returncode != 0:
    sys.stderr.write(r.stderr[:800])
    sys.exit(r.returncode)
