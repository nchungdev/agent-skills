#!/bin/bash
# Check OMV Media Stack Health
echo "=== 1. Aria2c Daemon ==="
systemctl is-active aria2.service && echo "Aria2 RPC: OK" || echo "Aria2 RPC: INACTIVE"

echo "=== 2. Core Containers ==="
sg docker -c 'docker ps --filter "name=radarr" --filter "name=sonarr" --filter "name=prowlarr" --filter "name=jellyseerr" --filter "name=plex" --filter "name=jellyfin" --filter "name=ariang" --filter "name=tdarr" --format "table {{.Names}}\t{{.Status}}"'

echo "=== 3. MergerFS MainPool ==="
df -h /srv/mergerfs/MainPool
