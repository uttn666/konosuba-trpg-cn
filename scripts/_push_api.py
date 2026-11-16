# -*- coding: utf-8 -*-
"""通过 GitHub REST Git Database API 推送本地提交（绕过 github.com:443 被阻断）。"""
import base64, json, os, subprocess, sys, tempfile

REPO = "uttn666/konosuba-trpg-cn"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(tempfile.gettempdir(), "ktpush")
os.makedirs(TMP, exist_ok=True)

def gh(*args, input_obj=None, raw=False, method=None):
    cmd = ["gh", "api"]
    if method:
        cmd += ["--method", method]
    cmd += list(args)
    if input_obj is not None:
        p = os.path.join(TMP, "payload.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(input_obj, f)
        cmd += ["--input", p]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    if r.returncode != 0:
        print("CMD FAILED:", " ".join(cmd))
        print("STDOUT:", (r.stdout or "")[:1500])
        print("STDERR:", (r.stderr or "")[:1500])
        sys.exit(1)
    return r.stdout if raw else json.loads(r.stdout)

def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    if r.returncode != 0:
        print("GIT FAILED:", args, r.stderr[:800]); sys.exit(1)
    return r.stdout

# 1. 远端基线
ref = gh(f"repos/{REPO}/git/ref/heads/main")
base_commit = ref["object"]["sha"]
base_tree = gh(f"repos/{REPO}/git/commits/{base_commit}")["tree"]["sha"]
print("base commit:", base_commit[:10])

# 2. 本地差异
out = git("-c", "core.quotepath=false", "diff", "--name-status", "origin/main", "HEAD")
entries = []
n_blob = 0
for line in out.splitlines():
    parts = line.split("\t")
    if len(parts) < 2:
        continue
    status, path = parts[0][0], parts[1]
    if status == "D":
        entries.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
        continue
    fp = os.path.join(ROOT, path)
    if not os.path.isfile(fp):
        print("missing file, skip:", path); continue
    with open(fp, "rb") as f:
        data = f.read()
    blob = gh(f"repos/{REPO}/git/blobs", method="POST", input_obj={"content": base64.b64encode(data).decode(), "encoding": "base64"})
    entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    n_blob += 1
    if n_blob % 10 == 0:
        print(f"  blobs uploaded: {n_blob}")
print("files:", len(entries), "blobs:", n_blob)

# 3. tree
tree = gh(f"repos/{REPO}/git/trees", method="POST", input_obj={"base_tree": base_tree, "tree": entries})
print("tree:", tree["sha"][:10])

# 4. commit（合并两个本地提交的信息）
msgs = git("log", "--format=%B%n---", "origin/main..HEAD")
message = "feat: 右侧常驻目录 + 移动端/平板适配 + PWA + 桌面版(Electron) + 安卓工程(Capacitor)\n\n" + msgs[:3000]
commit = gh(f"repos/{REPO}/git/commits", method="POST", input_obj={"message": message, "tree": tree["sha"], "parents": [base_commit]})
print("commit:", commit["sha"][:10])

# 5. 更新 ref
gh(f"repos/{REPO}/git/refs/heads/main", method="PATCH", input_obj={"sha": commit["sha"], "force": False})
print("ref updated")

# 6. 同步本地 origin/main
subprocess.run(["git", "update-ref", "refs/remotes/origin/main", commit["sha"]], cwd=ROOT)
print("DONE. remote main =", commit["sha"])
