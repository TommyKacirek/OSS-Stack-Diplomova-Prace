#!/bin/bash
echo "Starting manual backup..."
sudo /usr/local/bin/backup-cyberlab.sh
echo "Backup finished. Last 5 log entries:"
tail -n 5 /var/log/restic-backup.json
