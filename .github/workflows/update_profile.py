import os, re, json, urllib.request
from datetime import datetime, timezone

TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "User-Agent": "B-ER-U",
    "Accept": "application/vnd.github.v3+json"
}

def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def time_ago(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        diff = (datetime.now(timezone.utc) - dt).total_seconds()
        if diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff / 60)}m ago"
        elif diff < 86400:
            return f"{int(diff / 3600)}h ago"
        else:
            return f"{int(diff / 86400)}d ago"
    except:
        return "N/A"

def check_repo_has_code(owner, repo_name):
    """Check if a repo has actual code files (not just README)."""
    try:
        tree = api_get(f"https://api.github.com/repos/{owner}/{repo_name}/git/trees/HEAD?recursive=0")
        files = [t["path"] for t in tree.get("tree", [])]
        code_extensions = {".c", ".cpp", ".h", ".java", ".py", ".sh", ".mk", ".bp", ".rc", ".prop", ".xml", ".te", ".conf", ".cfg", ".config", ".dts", ".dtsi"}
        has_code = any(any(f.endswith(ext) for ext in code_extensions) for f in files)
        return has_code
    except:
        return False

# ---- Main ----
print("Fetching repos...")
all_repos = []
page = 1
while True:
    data = api_get(f"https://api.github.com/users/Il103/repos?per_page=100&page={page}&sort=updated")
    if not data:
        break
    all_repos.extend(data)
    if len(data) < 100:
        break
    page += 1

print(f"Found {len(all_repos)} repos")

# ---- Detect main project (X6886) ----
device_name = "Infinix Hot 60 Pro+"
device_repo = "android_device_infinix_x6886"
vendor_repo = "vendor_infinix_x6886"
kernel_repo = "kernel_infinix_x6886"
manifest_repo = "android_manifest_x6886"
recovery_repo = "twrp_device_infinix_X6886"

# Check status of each component
print("Checking component status...")
device_done = check_repo_has_code("Il103", device_repo)
vendor_done = check_repo_has_code("Il103", vendor_repo)
kernel_done = check_repo_has_code("Il103", kernel_repo)
manifest_done = check_repo_has_code("Il103", manifest_repo)
recovery_done = check_repo_has_code("Il103", recovery_repo)

print(f"  Device: {'Done' if device_done else 'Partial'}")
print(f"  Vendor: {'Done' if vendor_done else 'Partial'}")
print(f"  Kernel: {'Done' if kernel_done else 'Partial'}")
print(f"  Manifest: {'Done' if manifest_done else 'Partial'}")
print(f"  Recovery: {'Done' if recovery_done else 'Partial'}")

# Get default branches
def get_branch(repo):
    try:
        info = api_get(f"https://api.github.com/repos/Il103/{repo}")
        return info.get("default_branch", "main")
    except:
        return "main"

device_branch = get_branch(device_repo)
vendor_branch = get_branch(vendor_repo)
kernel_branch = get_branch(kernel_repo)
manifest_branch = get_branch(manifest_repo)
recovery_branch = get_branch(recovery_repo)

# ---- Build Current Project section ----
def badge(label, status, color):
    return f"[![{label}](https://img.shields.io/badge/{label}-{status}-{color}?style=flat-square)](https://github.com/Il103/{label.lower().replace(' ', '_').replace('/', '_')})"

status_badges = []
status_badges.append(f"[![Device Tree](https://img.shields.io/badge/Device%20Tree-{'Done' if device_done else 'Partial'}-{('3DDC84' if device_done else 'FFD700')}?style=flat-square)](https://github.com/Il103/{device_repo})")
status_badges.append(f"[![Vendor Tree](https://img.shields.io/badge/Vendor%20Tree-{'Done' if vendor_done else 'Partial'}-{('3DDC84' if vendor_done else 'FFD700')}?style=flat-square)](https://github.com/Il103/{vendor_repo})")
status_badges.append(f"[![Kernel](https://img.shields.io/badge/Kernel-{'Done' if kernel_done else 'Pending'}-{('3DDC84' if kernel_done else 'FF006E')}?style=flat-square)](https://github.com/Il103/{kernel_repo})")

project_section = f"""### <img src="https://fdn2.gsmarena.com/vv/pics/infinix/infinix-hot-60-pro-plus-2.jpg" width="40" height="40" style="vertical-align:middle; border-radius:8px;"/> {device_name} [![last](https://img.shields.io/github/last-commit/Il103/android_device_infinix_x6886?style=flat&color=00E5FF&label=)](https://github.com/Il103/android_device_infinix_x6886)

{" ".join(status_badges)}

| Repository | Branch | Status |
|------------|--------|--------|
| `{device_repo}` | `{device_branch}` | {"Done" if device_done else "Partial"} |
| `{vendor_repo}` | `{vendor_branch}` | {"Done" if vendor_done else "Partial"} |
| `{kernel_repo}` | `{kernel_branch}` | {"Done" if kernel_done else "Partial"} |
| `{manifest_repo}` | `{manifest_branch}` | {"Done" if manifest_done else "Partial"} |
| `{recovery_repo}` | `{recovery_branch}` | {"Done" if recovery_done else "Partial"} |
"""

# ---- Build Live Activity section ----
print("Building live activity...")
activity_repos = [
    device_repo, vendor_repo, kernel_repo, manifest_repo, recovery_repo
]
# Add other repos
for repo in all_repos:
    if repo["name"] not in activity_repos and not repo.get("fork", False):
        activity_repos.append(repo["name"])

activity_section = "| Repository | Last Commit | Time |\n"
activity_section += "|------------|-------------|------|\n"

for repo_name in activity_repos[:8]:
    try:
        commits = api_get(f"https://api.github.com/repos/Il103/{repo_name}/commits?per_page=1&author=Il103")
        if commits and isinstance(commits, list) and len(commits) > 0:
            c = commits[0]
            msg = c["commit"]["message"].split("\n")[0][:55]
            sha = c["sha"][:7]
            date = c["commit"]["committer"]["date"]
            short = repo_name.replace("android_", "").replace("infinix_", "").replace("x6886", "X6886")
            activity_section += f"| {short} | {msg} [{sha}](https://github.com/Il103/{repo_name}/commit/{sha}) | {time_ago(date)} |\n"
    except:
        pass

now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
activity_section += f"\n*Last updated: {now_str}*"

# ---- Read and update README ----
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

old_readme = readme

# Replace PROJECT section
readme = re.sub(
    r"<!-- PROJECT-START -->.*?<!-- PROJECT-END -->",
    f"<!-- PROJECT-START -->\n{project_section}\n<!-- PROJECT-END -->",
    readme, flags=re.DOTALL
)

# Replace LIVE section
readme = re.sub(
    r"<!-- LIVE-START -->.*?<!-- LIVE-END -->",
    f"<!-- LIVE-START -->\n{activity_section}\n<!-- LIVE-END -->",
    readme, flags=re.DOTALL
)

# Only write if changed
if readme != old_readme:
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print("README updated!")
else:
    print("No changes detected, skipping...")
    exit(0)
