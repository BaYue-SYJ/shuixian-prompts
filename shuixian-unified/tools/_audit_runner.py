#!/usr/bin/env python3
import subprocess, sys, os

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-unified-0920"
NODE = r"C:\Users\lianxiang\.workbuddy\binaries\node\versions\22.22.2-3\node.exe"
NMP = r"C:\Users\lianxiang\.workbuddy\binaries\node\workspace\node_modules"

SUITES = [
    "test_features", "test_i18n", "test_mobile_nav",
    "verify_lb_scroll", "verify_lb_edge", "verify_lb_pages",
    "verify_masonry", "verify_masonry_append", "verify_facets", "verify_facet_single",
    "verify_multi", "verify_import_newcat", "verify_detail_fit", "verify_prompt_full",
]

env = os.environ.copy()
env["NODE_PATH"] = NMP

results = []
for s in SUITES:
    p = os.path.join(ROOT, "tools", s + ".js")
    if not os.path.exists(p):
        results.append((s, "MISSING", ""))
        continue
    run_env = env.copy()
    try:
        r = subprocess.run([NODE, p], cwd=ROOT, env=run_env,
                           capture_output=True, text=True, timeout=180)
        out = (r.stdout + r.stderr).strip()
        status = "PASS" if r.returncode == 0 else "FAIL"
        # last few lines as evidence
        tail = "\n".join(out.splitlines()[-6:]) if out else "(no output)"
        results.append((s, status, tail))
    except subprocess.TimeoutExpired:
        results.append((s, "TIMEOUT", ""))

print("=" * 60)
for s, st, ev in results:
    print(f"[{st:6}] {s}")
    if st != "PASS":
        print("        " + ev.replace("\n", "\n        "))
print("=" * 60)
fails = [s for s, st, _ in results if st != "PASS"]
print(f"TOTAL {len(results)}  PASS {len(results)-len(fails)}  FAIL {len(fails)}")
sys.exit(1 if fails else 0)
