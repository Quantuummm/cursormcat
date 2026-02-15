"""Set up Firebase project: add Firebase, create web app, get config."""
import os, json, time
from google.oauth2 import service_account
import google.auth.transport.requests
import requests

SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/firebase',
]
KEY = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS",
                      r"C:\Users\Rauf\AppData\Roaming\Code\CloudKey.json")

creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
creds.refresh(google.auth.transport.requests.Request())
project = creds.project_id
headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}

# 1. Add Firebase ─────────────────────────────────────
print("1. Adding Firebase to GCP project...")
url = f"https://firebase.googleapis.com/v1beta1/projects/{project}:addFirebase"
resp = requests.post(url, headers=headers)
if resp.status_code == 200:
    op = resp.json()
    print("   Operation started:", op.get("name", ""))
    # Poll until done
    op_url = f"https://firebase.googleapis.com/v1beta1/{op['name']}"
    for _ in range(30):
        time.sleep(2)
        r = requests.get(op_url, headers=headers)
        if r.json().get("done"):
            print("   Firebase added!")
            break
    else:
        print("   Timed out waiting for Firebase setup")
elif resp.status_code == 409:
    print("   Already a Firebase project")
else:
    print(f"   Status {resp.status_code}: {resp.text[:200]}")

# 2. Create web app ───────────────────────────────────
print("\n2. Checking web apps...")
url = f"https://firebase.googleapis.com/v1beta1/projects/{project}/webApps"
resp = requests.get(url, headers=headers)
apps = resp.json().get("apps", [])

if apps:
    app_id = apps[0]["appId"]
    name = apps[0].get("displayName", "unnamed")
    print(f"   Found existing web app: {name} ({app_id})")
else:
    print("   Creating web app 'MCAT Mastery'...")
    resp = requests.post(url, headers=headers, json={"displayName": "MCAT Mastery"})
    if resp.status_code == 200:
        op = resp.json()
        op_url = f"https://firebase.googleapis.com/v1beta1/{op['name']}"
        for _ in range(30):
            time.sleep(2)
            r = requests.get(op_url, headers=headers)
            data = r.json()
            if data.get("done"):
                result = data.get("response", {})
                app_id = result.get("appId", "")
                print(f"   Created! appId: {app_id}")
                break
        else:
            print("   Timed out")
            app_id = None
    else:
        print(f"   Error {resp.status_code}: {resp.text[:200]}")
        app_id = None

# 3. Get config ───────────────────────────────────────
if app_id:
    print("\n3. Fetching web app config...")
    config_url = f"https://firebase.googleapis.com/v1beta1/projects/{project}/webApps/{app_id}/config"
    resp = requests.get(config_url, headers=headers)
    if resp.status_code == 200:
        config = resp.json()
        print(json.dumps(config, indent=2))
        
        # Save to file
        out_path = os.path.join(os.path.dirname(__file__), "..", "firebase_config.json")
        with open(out_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"\n   Config saved to firebase_config.json")
    else:
        print(f"   Error {resp.status_code}: {resp.text[:200]}")

# 4. Enable anonymous auth ────────────────────────────
print("\n4. Enabling anonymous authentication...")
# Identity Toolkit Admin API
url = f"https://identitytoolkit.googleapis.com/admin/v2/projects/{project}/config"
resp = requests.get(url, headers=headers)
if resp.status_code == 200:
    config_data = resp.json()
    print("   Auth config retrieved OK")
    
    # Enable anonymous provider
    url2 = f"https://identitytoolkit.googleapis.com/admin/v2/projects/{project}/defaultSupportedIdpConfigs/anonymous"
    resp2 = requests.get(url2, headers=headers)
    if resp2.status_code == 404:
        # Need to create it
        url3 = f"https://identitytoolkit.googleapis.com/admin/v2/projects/{project}/inboundSamlConfigs"
        print("   Attempting to enable anonymous auth via Identity Platform...")
        anon_url = f"https://identitytoolkit.googleapis.com/v2/projects/{project}/config"
        patch_body = {
            "signIn": {
                "anonymous": {"enabled": True}
            }
        }
        r = requests.patch(anon_url, headers=headers, json=patch_body,
                          params={"updateMask": "signIn.anonymous.enabled"})
        if r.status_code == 200:
            print("   Anonymous auth enabled!")
        else:
            print(f"   Status {r.status_code}: {r.text[:200]}")
    else:
        print(f"   Anonymous auth status: {resp2.status_code}")
else:
    print(f"   Status {resp.status_code}: {resp.text[:200]}")

print("\nDone!")
