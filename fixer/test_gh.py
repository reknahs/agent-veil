import os
import requests

token = os.environ.get("GITHUB_TOKEN")
print(f"Token length: {len(token) if token else 0}")
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
}
r = requests.get("https://api.github.com/user", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print(f"User: {r.json().get('login')}")
else:
    print(f"Error: {r.text}")
