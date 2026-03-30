import requests
import xml.etree.ElementTree as ET

PRESET_NAME = "plex"

def get_data(host, config={}):
    try:
        token = config.get("token", "")
        r = requests.get(
            f"http://{host}:32400/status/sessions?X-Plex-Token={token}",
            timeout=5
        )
        root = ET.fromstring(r.text)
        sessions = int(root.attrib.get("size", 0))
        return {"active_streams": sessions, "status": "online"}
    except Exception as e:
        return {"status": "offline", "error": str(e)}