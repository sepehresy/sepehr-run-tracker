import requests
import json

def load_gist_data(gist_id, filename, token):
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        gist = response.json()
        files = gist.get("files", {})
        file_obj = files.get(filename)
        if file_obj and "content" in file_obj:
            try:
                return json.loads(file_obj["content"])
            except Exception as e:
                print("Failed to parse Gist file content as JSON:", e)
                print("Raw content:", file_obj["content"])
                return {}
    print(f"Failed to load gist: {response.status_code} {response.text}")
    return {}

def save_gist_data(gist_id, filename, token, data):
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {token}"}
    payload = {"files": {filename: {"content": json.dumps(data, indent=2)}}}
    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code == 200
