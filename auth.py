import json
import os

import requests

from firebase_admin import credentials as fb_creds
from google.oauth2 import service_account


class AuthManager:

    def __init__(self, auth:list=["g"]):
        self.creds = {}
        try:
            # load creds local
            self.bq_path =r"C:\Users\wired\OneDrive\Desktop\Projects\qfs\aixr-401704-59fb7f12485c.json" if os.name == "nt" else "aixr-401704-59fb7f12485c.json"
            self.fb_path = r"C:\Users\wired\OneDrive\Desktop\BestBrain\firebase_creds.json" if os.name == "nt" else "firebase_creds.json"

            if "g" in auth:
                bq_quth_payload = self._set_creds(self.bq_path)
            elif "fb" in auth:
                fb_auth_payload = self._set_creds(self.fb_path)


        except Exception as e:
            print(f"Could not load creds local (exception: {e}) request from server")
            domain = "http://127.0.0.1:8000" if os.name == "nt" else f"https://{os.environ.get('DMOAIN')}"
            self.auth_request_path = f"{domain}/auth/access"

            request_types = []

            if "g" in auth:
                request_types.append("g_creds")
            elif "fb" in auth:
                request_types.append("fb_creds")

            self.creds_response = requests.post(
                self.auth_request_path,
                data={
                    "types": request_types
                })

            if "g" in auth:
                fb_auth_payload = self.creds_response["g_creds"]
            elif "fb" in auth:
                bq_quth_payload = self.creds_response["fb_creds"]

        if "g" in auth:
            self.creds["g"] = service_account.Credentials.from_service_account_info(bq_quth_payload)

        elif "fb" in auth:
            self.creds["fb"] = fb_creds.Certificate(fb_auth_payload)

        print("finished loading creds")


    def _set_creds(self, path):
        fb_creds = os.environ.get("FIREBASE_CREDENTIALS")
        try:
            fb_creds = json.loads(fb_creds)
        except Exception as e:
            print(f"Failed loading FIREBASE_CREDENTIALS from env (ERROR:{e}), trying directly from file")
            with open(path, "r", encoding="utf-8") as f:
                fb_creds = json.load(f)
        return fb_creds