#!/bin/bash

LOG_DIRECTORY="/var/log/backup_logs"
LOG="/var/log/backup_logs/root.log"

function timestamp() {
    echo [$(date '+%Y-%m-%d %H:%M:%S')]
}

function log() {
    echo -e "$(timestamp) $1" >> $LOG
}

function log_error() {
    echo -e "$(timestamp) ERROR: $1" >> $LOG
}

if [ ! -d ${LOG_DIRECTORY} ]; then
    mkdir ${LOG_DIRECTORY}
fi

if [ ! -e ${LOG} ]; then
    touch ${LOG}
    log "Creating log file for backup"
fi

DEL=""

while getopts ":d" opt; do
    case $opt in
        d)
            DEL="--delete"
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done

log "Starting backup procedure"

TARGET_HOST="pascal_arch"
TARGET_DIR="/mybook"

ping -c 1 ${TARGET_HOST} > /dev/null 2>&1

if [ ! $? -eq 0 ]; then
    log_error "Unable to comunicate with nfs host"
    exit 1
fi

BACKUP_MOUNT="/mnt/nfs/mybook"

if [ ! -d ${BACKUP_MOUNT} ]; then
    log "Creating mount point for backup device"
    mkdir -p ${BACKUP_MOUNT}
fi

unmount=false

if ! mountpoint -q ${BACKUP_MOUNT}; then
    log "Mounting backup device"
    mount ${BACKUP_MOUNT}

    if [ ! $? -eq 0 ]; then
        log_error "Unable to mount backup device"
        exit 2
    fi

    unmount=true
fi

BACKUP_DIR="${BACKUP_MOUNT}/Linux_Backups/xps13_arch"

if [ ! -d ${BACKUP_DIR} ]; then
    log "Creating backup directory on backup device"
    mkdir -p ${BACKUP_DIR}
fi

INFO="flist,stats2"

# rsync -aAX ${DEL} --info=${INFO} --exclude={"/dev/*","/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/hdd/*","/srv/*","/lost+found"} / ${BACKUP_DIR} | ts '[%Y-%m-%d %H:%M:%S]' >> $LOG

# Todo: Make actual backup

if [ "$unmount" = true ]; then
    log "Unmounting the backup device"
    umount ${BACKUP_MOUNT}
fi

log "Finishing backup procedure"
echo "" >> $LOG
