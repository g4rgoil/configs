#!/bin/bash

LOG="/var/log/backup_logs/root.log"
DEL=false

while getopts ":d" opt; do
    case $opt in
        d)
            DEL=true
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done

echo "$(date)" >> $LOG

if ! mountpoint -q /hdd/mybook; then
    echo "Backup device not mounted" >> $LOG
    exit 2
fi

if [ "$DEL" = true ]; then
    rsync -aAXv --delete --exclude={"/dev/*","/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/hdd/*","/lost+found"} / /hdd/mybook/Linux_Backups/desktop_arch/ >> $LOG
else
    rsync -aAXv --exclude={"/dev/*","/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/hdd/*","/lost+found"} / /hdd/mybook/Linux_Backups/desktop_arch/ >> $LOG
fi

echo -en "\n" >> $LOG
