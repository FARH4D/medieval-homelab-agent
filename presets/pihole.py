import requests

PRESET_NAME = "pihole"

def get_data(host, config={}):
    try:
        r = requests.get(
            f"http://{host}/admin/api.php?summary&auth={config.get('token', '')}",
            timeout=5
        )
        data = r.json()
        return {
            "queries_today": data.get("dns_queries_today"),
            "ads_blocked": data.get("ads_blocked_today"),
            "status": "online"
        }
    except:
        return {"status": "offline"}