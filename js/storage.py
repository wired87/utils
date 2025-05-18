import requests
import os

def download_threejs(url: str, save_path: str = "static/js/three.min.js"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Three.js gespeichert unter: {save_path}")
    else:
        print(f"❌ Download fehlgeschlagen (Status {response.status_code})")


THREE_JS_URL = "https://cdn.jsdelivr.net/npm/three@0.157.0/build/three.min.js"
FIREBASE_APP= r"https://www.gstatic.com/firebasejs/9.22.2/firebase-app-compat.js"
FIREBASE_DB= r"https://www.gstatic.com/firebasejs/9.22.2/firebase-database-compat.js"


if __name__ == "__main__":
    download_threejs(
        url=FIREBASE_DB,
        save_path=rf"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\static\{FIREBASE_DB.split('/')[-1]}" if os.name == "nt" else f"static/{FIREBASE_DB.split('/')[-1]}"
    )