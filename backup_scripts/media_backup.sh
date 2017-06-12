#!/bin/bash

LOG="/var/log/backup_logs/media.log"

echo "$(date)" >> $LOG

if ! mountpoint -q /hdd/mybook; then
    echo "ERROR: Backup device not mounted" >> $LOG
    exit 2
fi

rsync -aAXv --exclude={"System Volume Information","game_saves"} /hdd/media/ /hdd/mybook/HDD_Backups/media >> $LOG

echo -en "\n" >> $LOG
