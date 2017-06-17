#!/bin/bash

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

function log_output() {
    awk -v date="$(timestamp)" '{print date, $0}' >> $LOG
}

if [ ! -d /var/log/backup_logs ]; then
    mkdir /var/log/backup_logs
    log "Creating backup log directory"
fi

log "Starting backup procedure"

TARGET_HOST="pascal_arch"
TARGET_DIR="/mybook"

ping -c 1 $TARGET_HOST > /dev/null 2>&1

if [ ! $? -eq 0 ]; then
    log_error "Unable to comunicate with server"
    exit 1
fi

BACKUP_MOUNT="/mnt/nfs/mybook"

if [ ! -d ${BACKUP_MOUNT} ]; then
    log "Creating backup mount point"
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

EXCLUDE='{"/dev/*","/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/hdd/*","/lost+found"}'
INFO="flist,stats2"

# rsync -aAX --info=${INFO} --exclude=${EXCLUDE} / ${BACKUP_DIR} | log_output

# Todo: Make actual backup

if [ "$unmount" = true ]; then
    log "Unmounting the backup device"
    umount ${BACKUP_MOUNT}
fi

log "Finishing backup procedure"
echo "" >> $LOG
