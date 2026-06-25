#!/bin/bash
CONFIG="/home/cate/cate-PA/src/stations.json"
FS1_IP=$(python3 -c "import json; print(json.load(open('$CONFIG'))['FS1'])")
SELF_IP=$(hostname -I | awk '{print $1}')

if [ "$SELF_IP" != "$FS1_IP" ]; then
    echo "This station's Raspberry Pi does not have permission to reboot all stations."
    exit 1
fi

for ip in $(python3 -c "import json; [print(ip) for ip in json.load(open('/home/cate/cate-PA/src/stations.json')).values()]"); do
    if [ "$ip" != "$FS1_IP" ]; then
        echo "Rebooting $ip..."
        ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no cate@$ip "sudo reboot" &
    fi
done

wait
echo "All stations rebooted."