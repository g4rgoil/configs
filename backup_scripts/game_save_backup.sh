#!/bin/bash

if [ ! -d /var/log/backup_logs ]; then
    mkdir /var/log/backup_logs
fi

LOG="/var/log/backup_logs/media.log"

echo "$(date)" >> $LOG

if ! mountpoint -q /hdd/mybook; then
    echo "ERROR: Backup device not mounted" >> $LOG
    exit 2
fi

rsync -aAXv /hdd/media/game_saves/ /hdd/mybook/GameSaveManager/ >> $LOG

echo -en "\n" >> $LOG
