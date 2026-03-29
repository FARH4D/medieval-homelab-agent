import requests

PRESET_NAME = "plex"

def get_data(host, config={}):
    try:
        token = config.get("token", "")
        r = requests.get(
            f"http://{host}:32400/status/sessions?X-Plex-Token={token}",
            timeout=5
        )
        sessions = r.json().get("MediaContainer", {}).get("size", 0)
        return {"active_streams": sessions, "status": "online"}
    except:
        return {"status": "offline"}