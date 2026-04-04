import docker
import requests
import time
import os
from presets import PRESETS
from presets.generic import get_data as generic_get_data

MASTERMIND_URL = os.environ.get("MASTERMIND_URL", "http://192.168.1.100:8000/report")
VM_NAME = os.environ.get("VM_NAME", "unknown-vm")
VM_HOST = os.environ.get("VM_HOST", "localhost")
INTERVAL = int(os.environ.get("INTERVAL", "30"))

client = docker.from_env()

# API keys/tokens passed in as env vars per service
# e.g. PRESET_CONFIG_PLEX_TOKEN=abc123
def get_config_for(service_name):
    prefix = f"PRESET_CONFIG_{service_name.upper()}_"
    return {
        k.replace(prefix, "").lower(): v
        for k, v in os.environ.items()
        if k.startswith(prefix)
    }

def get_base_name(container_name):
    # immich_server -> immich, sonarr-1 -> sonarr
    return container_name.lower().split("_")[0].split("-")[0]

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

def group_containers(containers):
    groups = {}
    for container in containers:
        base = get_base_name(container.name)
        if base not in groups:
            groups[base] = {
                "containers": [],
                "any_unhealthy": False
            }
        groups[base]["containers"].append(container)
        if container.status != "running":
            groups[base]["any_unhealthy"] = True
    return groups

def collect():
    containers = client.containers.list()
    groups = group_containers(containers)
    services = []

    for base_name, group in groups.items():
        # Skip the agent itself
        if "agent" in base_name:
            continue

        # Use stats from the primary container (first one)
        primary = group["containers"][0]
        stats = get_container_stats(primary)

        # Determine overall status
        status = "degraded" if group["any_unhealthy"] else "running"

        # Check for preset match
        preset_key = next((k for k in PRESETS if k in base_name), None)
        if preset_key:
            config = get_config_for(preset_key)
            rich_data = PRESETS[preset_key](VM_HOST, config)
        else:
            rich_data = generic_get_data(VM_HOST)

        # Note how many containers are in this group
        container_count = len(group["containers"])

        services.append({
            "name": base_name,
            "status": status,
            "preset": preset_key if preset_key else "generic",
            "container_count": container_count,
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