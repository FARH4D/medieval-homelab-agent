import requests

PRESET_NAME = "sonarr"

def get_data(host, config={}):
    try:
        r = requests.get(
            f"http://{host}:8989/api/v3/queue",
            headers={"X-Api-Key": config.get("api_key", "")},
            timeout=5
        )
        return {"queue_size": len(r.json().get("records", [])), "status": "online"}
    except:
        return {"status": "offline"}