#!/bin/bash

slack_url="https://hooks.slack.com/services/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"
script_directory="/etc/backup_scripts"
log_directory="/var/log/backup_logs"
log="$log_directory/root.log"
tformat="%Y-%m-%d %H:%M:%S"

function timestamp() {
    echo ["$(date "+${tformat}")"]
}

function log() {
    echo -e "$(timestamp) $1" >> $log
}

function log_error() {
    echo -e "$(timestamp) ERROR: $1" >> $log
}

function slack_message() {
    curl -X POST --data-urlencode "payload={\"text\": \"${1}\"}" ${slack_url} > /dev/null 2>&1
}

if [[ ! -d ${log_directory} ]]; then
    mkdir -p ${log_directory}
    log "Creating backup log directory"
fi


log "Starting backup procedure"

backup_mount="/hdd/mybook"

if [[ ! -d ${backup_mount} ]]; then
    log "Creating mount point for backup device"
    mkdir -p ${backup_mount}
fi


unmount=false

if ! mountpoint -q ${backup_mount}; then
    log "Mounting backup device"

    if ! mount ${backup_mount}; then
        log_error "Unable to mount backup device"
        slack_message "$(hostname): Backup failed, unable to mount backup target."
        exit 2
    fi

    if ! mountpoint -q ${backup_mount}; then
        log_error "Unable to mount backup device"
        slack_message "$(hostname): Backup failed, unable to mount backup target."
        exit 2
    fi

    unmount=true
fi


backup_repo="${backup_mount}/Borg_Backups/pascal_desktop"

if [[ ! -d "${backup_repo}" ]]; then
    log_error "Borg repository doesn't exist"
    slack_message "$(hostname): Backup failed, borg repository doesn't exist."
    exit 2
fi

export BORG_REPO=${backup_repo}
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/pascal_desktop"


log "Creating backup"

exclude_file="${script_directory}/root_backup.exclude"

borg create                 \
    --warning               \
    --stats                 \
    --list                  \
    --filter E              \
    --stats                 \
    --compression lz4       \
    --exclude-from ${exclude_file}  \
                            \
    ::'pascal_desktop-{now}'    \
    / 2>&1 | ts "[${tformat}]" >> $log

backup_exit=$?


log "Pruning borg repository"

borg prune                  \
    --list                  \
    --prefix 'pascal_desktop-'  \
    --keep-daily    7       \
    --keep-weekly   4       \
    --keep-monthly  6       \
    2>&1 | ts "[${tformat}]" >> $log

prune_exit=$?


global_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [[ ${global_exit} -eq 1 ]]; then
    log_error "Backup or Prune exited with a warning"
elif [[ ${global_exit} -gt 1 ]]; then
    log_error "Backup or Prune exited with an error"
fi


if [[ "$unmount" = true ]]; then
    log "Unmounting backup device"
    umount ${backup_mount}
fi

log "Finishing backup procedure"
echo "" >> $log

exit ${global_exit}
