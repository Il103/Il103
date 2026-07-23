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

def get_repo_info(owner, repo_name):
    """Get repo info including recent commits and file structure."""
    try:
        info = api_get(f"https://api.github.com/repos/{owner}/{repo_name}")

        # Get default branch
        default_branch = info.get("default_branch", "main")

        # Get recent commits by Il103
        commits = api_get(f"https://api.github.com/repos/{owner}/{repo_name}/commits?per_page=3&author=Il103")

        # Get top-level tree to detect file types
        tree = api_get(f"https://api.github.com/repos/{owner}/{repo_name}/git/trees/{default_branch}?recursive=0")
        files = [t["path"] for t in tree.get("tree", [])]

        # Detect status: has code files beyond just README/docs?
        code_extensions = {".c", ".cpp", ".h", ".java", ".py", ".sh", ".mk", ".bp", ".rc", ".prop", ".xml", ".te", ".conf", ".cfg", ".config", ".dts", ".dtsi"}
        has_code = any(any(f.endswith(ext) for ext in code_extensions) for f in files)
        has_readme = any("README" in f.upper() for f in files)

        # Detect what kind of tree this is
        tree_type = "unknown"
        if "BoardConfig.mk" in files or "device.mk" in files:
            tree_type = "device"
        elif "AndroidProducts.mk" in files or "vendor.mk" in files:
            tree_type = "vendor"
        elif "Makefile" in files or "Kconfig" in files or any(f.startswith("arch/") for f in files):
            tree_type = "kernel"
        elif "Android.mk" in files and any("twrp" in f.lower() for f in files):
            tree_type = "recovery"
        elif "x6886.xml" in files or "manifest.xml" in files:
            tree_type = "manifest"

        return {
            "name": repo_name,
            "type": tree_type,
            "has_code": has_code,
            "has_readme": has_readme,
            "files": files,
            "commits": commits if isinstance(commits, list) else [],
            "default_branch": default_branch,
            "description": info.get("description", ""),
            "updated_at": info.get("updated_at", ""),
            "stars": info.get("stargazers_count", 0)
        }
    except Exception as e:
        return {"name": repo_name, "type": "unknown", "has_code": False, "commits": [], "files": [], "error": str(e)}

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

# ---- Detect projects ----
# A "project" is a group of repos that share a device name pattern
# Patterns: android_device_*, vendor_*, kernel_*, *_device_*
projects = {}

for repo in all_repos:
    name = repo["name"]

    # Detect device name from repo name
    device_name = None
    repo_type = None

    if name.startswith("android_device_"):
        parts = name.replace("android_device_", "")
        device_name = parts
        repo_type = "device"
    elif name.startswith("vendor_"):
        parts = name.replace("vendor_", "")
        device_name = parts
        repo_type = "vendor"
    elif name.startswith("kernel_"):
        parts = name.replace("kernel_", "")
        device_name = parts
        repo_type = "kernel"
    elif name.startswith("android_manifest_"):
        parts = name.replace("android_manifest_", "")
        device_name = parts
        repo_type = "manifest"
    elif "twrp" in name and "device" in name:
        # twrp_device_infinix_X6886 -> extract device
        parts = name.split("_")
        for i, p in enumerate(parts):
            if p == "device" and i + 2 < len(parts):
                device_name = "_".join(parts[i+1:])
                repo_type = "recovery"
                break

    if device_name:
        if device_name not in projects:
            projects[device_name] = {}
        projects[device_name][repo_type] = {
            "repo": name,
            "info": repo,
            "full_info": None  # will fill below
        }

print(f"Found {len(projects)} project(s): {list(projects.keys())}")

# ---- Get detailed info for project repos ----
for device_name, components in projects.items():
    for comp_type, comp_data in components.items():
        full = get_repo_info("Il103", comp_data["repo"])
        comp_data["full_info"] = full
        print(f"  {device_name}/{comp_type}: {comp_data['repo']} - has_code={full.get('has_code', False)}, commits={len(full.get('commits', []))}")

# ---- Build Current Project section ----
project_section = "**Recent Activity**\n\n"

for device_name, components in projects.items():
    # Pick the most recent project (by updated_at)
    latest_update = ""
    for comp_type, comp_data in components.items():
        updated = comp_data["info"].get("updated_at", "")
        if updated > latest_update:
            latest_update = updated

    project_section += f"### {device_name.upper()}\n\n"

    # Status badges
    status_parts = []
    for comp_type in ["device", "vendor", "kernel", "manifest", "recovery"]:
        if comp_type in components:
            full = components[comp_type]["full_info"]
            has_code = full.get("has_code", False) if full else False
            status = "Done" if has_code else "Partial"
            color = "3DDC84" if has_code else "FFD700"
            label = comp_type.capitalize()
            if comp_type == "recovery":
                label = "Recovery"
            elif comp_type == "manifest":
                label = "Manifest"
            elif comp_type == "device":
                label = "Device Tree"
            elif comp_type == "vendor":
                label = "Vendor Tree"
            elif comp_type == "kernel":
                label = "Kernel"
            status_parts.append(f"[![{label}](https://img.shields.io/badge/{label}-{status}-{color}?style=flat-square)](https://github.com/Il103/{components[comp_type]['repo']})")

    project_section += " ".join(status_parts) + "\n\n"

    # Repos table
    project_section += "| Repository | Branch | Status |\n"
    project_section += "|------------|--------|--------|\n"

    for comp_type in ["device", "vendor", "kernel", "manifest", "recovery"]:
        if comp_type in components:
            repo_name = components[comp_type]["repo"]
            branch = components[comp_type]["info"].get("default_branch", "main")
            full = components[comp_type]["full_info"]
            has_code = full.get("has_code", False) if full else False
            status = "Done" if has_code else "Partial"
            project_section += f"| `{repo_name}` | `{branch}` | {status} |\n"

    project_section += "\n"

# ---- Build Live Activity section ----
activity_section = "**Recent Activity**\n\n"
activity_section += "| Repository | Last Commit | Time |\n"
activity_section += "|------------|-------------|------|\n"

activity_repos = [r["name"] for r in all_repos if not r.get("fork", False)]
activity_repos.sort(key=lambda x: next((comp["info"].get("updated_at", "") for comps in projects.values() for comp in comps.values() if comp["repo"] == x), ""), reverse=True)

for repo_name in activity_repos[:6]:
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
