#!/bin/bash
FS1_IP="128.127.1.50"
LOCAL_CONFIG="/home/cate/cate-PA/src/stations.json"
HOSTNAME=$(hostname)

if echo "$HOSTNAME" | grep -qi "fs1"; then
    echo "This is FS1, skipping config fetch."
    exit 0
fi

scp -o ConnectTimeout=5 -o StrictHostKeyChecking=no cate@${FS1_IP}:/home/cate/cate-PA/src/stations.json "$LOCAL_CONFIG" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Updated stations.json from FS1."
else
    echo "Could not reach FS1, using existing stations.json."
fi