import urllib.request
import urllib.error
import json
import os

TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_TOKEN_HERE")
OWNER = "chandrangshuadhikary"
REPO = "NHAA-Prototype-"
USERS = ["Debjit1mondal", "biswajitbasuli744-byte", "avilashgorai51-cyber"]

for user in USERS:
    print(f"Adding {user}...")
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/collaborators/{user}"
    req = urllib.request.Request(url, method="PUT")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    
    try:
        with urllib.request.urlopen(req) as response:
            print(response.status, response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}")

