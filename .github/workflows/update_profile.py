import os, re, json, time, urllib.request
from datetime import datetime, timezone

TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {TOKEN}", "User-Agent": "B-ER-U", "Accept": "application/vnd.github.v3+json"}

def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def get_recent_commit(repo):
    try:
        data = api_get(f"https://api.github.com/repos/{repo}/commits?per_page=1&author=Il103")
        if not data:
            return None
        c = data[0]
        return {
            "msg": c["commit"]["message"].split("\n")[0][:55],
            "sha": c["sha"][:7],
            "date": c["commit"]["committer"]["date"],
            "url": f"https://github.com/{repo}/commit/{c['sha'][:7]}"
        }
    except:
        return None

def time_ago(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        diff = (datetime.now(timezone.utc) - dt).total_seconds()
        if diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff/60)}m ago"
        elif diff < 86400:
            return f"{int(diff/3600)}h ago"
        else:
            return f"{int(diff/86400)}d ago"
    except:
        return "N/A"

# Read README
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

# Check last update time
last_match = re.search(r"Last updated: ([^\*]+)", readme)
if last_match:
    last_str = last_match.group(1).strip()
    try:
        last_dt = datetime.fromisoformat(last_str.replace(" UTC", "+00:00").replace(" ", "T", 1))
        elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
        if elapsed < 50:
            print(f"Last update was {int(elapsed)}s ago, sleeping...")
            exit(0)
    except:
        pass

# Check for new activity
REPOS = [
    "Il103/android_device_infinix_x6886",
    "Il103/vendor_infinix_x6886",
    "Il103/kernel_infinix_x6886",
    "Il103/android_manifest_x6886",
    "Il103/Il103"
]

has_new = False
last_dt_ref = None
if last_match:
    try:
        last_dt_ref = datetime.fromisostring(last_match.group(1).strip().replace(" UTC", "+00:00").replace(" ", "T", 1))
    except:
        pass

for repo in REPOS:
    commit = get_recent_commit(repo)
    if commit and commit["date"]:
        try:
            commit_dt = datetime.fromisoformat(commit["date"].replace("Z", "+00:00"))
            if last_dt_ref and commit_dt > last_dt_ref:
                has_new = True
                break
        except:
            pass

if not has_new and last_dt_ref:
    print("No new activity, sleeping...")
    exit(0)

print("New activity detected, updating...")

# Build table
now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
lines = ["**Recent Activity**", "", "| Repository | Last Commit | Time |", "|------------|-------------|------|"]

for repo in REPOS:
    repo_name = repo.split("/")[1]
    short = repo_name.replace("android_", "").replace("infinix_", "").replace("x6886", "X6886")
    commit = get_recent_commit(repo)
    if commit:
        lines.append(f"| {short} | {commit['msg']} [{commit['sha']}]({commit['url']}) | {time_ago(commit['date'])} |")
    else:
        lines.append(f"| {short} | No commits | N/A |")

lines.append("")
lines.append(f"*Last updated: {now_str}*")

table = "\n".join(lines)

# Replace live section
replacement = f"<!-- LIVE-START -->\n{table}\n<!-- LIVE-END -->"
readme_new = re.sub(r"<!-- LIVE-START -->.*?<!-- LIVE-END -->", replacement, readme, flags=re.DOTALL)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme_new)

print("Profile updated with", len(REPOS), "repos")
