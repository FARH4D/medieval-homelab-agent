import docker
import requests
import time
import os
from presets import PRESETS
from presets.generic import get_data as generic_get_data

MASTERMIND_URL = os.environ.get("MASTERMIND_URL", "http://192.168.1.100:8000/report")
VM_NAME = os.environ.get("VM_NAME", "unknown-vm")
INTERVAL = int(os.environ.get("INTERVAL", "30"))

# API keys/tokens passed in as env vars per service
# e.g. PRESET_CONFIG_PLEX_TOKEN=abc123
def get_config_for(service_name):
    prefix = f"PRESET_CONFIG_{service_name.upper()}_"
    return {
        k.replace(prefix, "").lower(): v
        for k, v in os.environ.items()
        if k.startswith(prefix)
    }

client = docker.from_env()

def get_container_stats(container):
    try:
        stats = container.stats(stream=False)
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                    stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                       stats["precpu_stats"]["system_cpu_usage"]
        cpu_percent = (cpu_delta / system_delta) * 100
        mem_usage = stats["memory_stats"]["usage"]
        mem_limit = stats["memory_stats"]["limit"]
        mem_percent = (mem_usage / mem_limit) * 100
        return {
            "cpu_percent": round(cpu_percent, 2),
            "mem_percent": round(mem_percent, 2)
        }
    except:
        return {"cpu_percent": 0, "mem_percent": 0}

def collect():
    containers = client.containers.list()
    services = []

    for container in containers:
        name = container.name.lower()
        host = os.environ.get("VM_HOST", "localhost")
        stats = get_container_stats(container)

        preset_key = next((k for k in PRESETS if k in name), None)

        if preset_key:
            config = get_config_for(preset_key)
            rich_data = PRESETS[preset_key](host, config)
        else:
            rich_data = generic_get_data(host)

        services.append({
            "name": name,
            "status": container.status,
            "preset": preset_key if preset_key else "generic",
            "stats": stats,
            "data": rich_data
        })

    payload = {
        "vm": VM_NAME,
        "timestamp": time.time(),
        "services": services
    }

    try:
        r = requests.post(MASTERMIND_URL, json=payload, timeout=5)
        print(f"[{VM_NAME}] Reported {len(services)} services → {r.status_code}")
    except Exception as e:
        print(f"[{VM_NAME}] Failed to reach mastermind: {e}")

while True:
    collect()
    time.sleep(INTERVAL)