#!/bin/bash

script_directory="/etc/backup_scripts"
# script_file="${script_directory}/desktop_backup.sh"
exclude_file="${script_directory}/root.exclude"
library_file="${script_directory}/backup_library.sh"

# shellcheck source=/dev/null
source $library_file

log_directory="/var/log/backup_logs"
ts_file="${log_directory}/desktop.ts"
log_file="${log_directory}/root.log"

pid_file="/var/run/desktop-backup.pid"

min_backup_interval="-6 hours"
time_reference_file=$(mktemp)

backup_mount="/hdd/mybook"
unmount=false

export BORG_REPO="${backup_mount}/Borg_Backups/pascal_desktop"
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/mybook_desktop"

function mount_backup_device() {
    log "Mounting backup device"

    if ! mount $backup_mount || ! mountpoint -q $backup_mount; then
        log_error "Unable to mount backup device"
        slack_message "Backup failed, unable to mount backup target."
        exit 2
    fi

    unmount=true
}

function unmount_backup_device() {
    if [[ "$unmount" = true ]]; then
        log "Unmounting backup device"
        umount $backup_mount
    fi

    unmount=false
}

function finish() {
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        date +%Y%m%d%H%M > $ts_file
    fi

    unmount_backup_device
    
    if [[ $exit_code -eq 0 ]]; then
        log "Finishing backup procedure"
    else
        log "Backup procedure failed"
    fi
    blank_line
}

function terminate() {
    log_error "The backup procedure was terminated by a signal"
    unmount_backup_device
    blank_line
}

trap finish EXIT

trap 'trap "" EXIT; terminate' \
    HUP INT QUIT TERM


if [[ -f $pid_file ]] && kill -0 "$(cat $pid_file)" 2>/dev/null; then
    echo "Different instance of backup already running"
    exit 0
fi

echo $$ > $pid_file

if [[ ! -d $log_directory ]]; then
    log "Creating backup log directory"
    mkdir -p $log_directory
fi

if [[ ! -d $backup_mount ]]; then
    log "Creating mount point for backup device"
    mkdir -p $backup_mount
fi


log "Starting backup procedure"


if [[ -f $ts_file ]]; then
    touch -t "$(<$ts_file)" $ts_file
    touch -d "$min_backup_interval" "$time_reference_file"

    if [[ $ts_file -nt $time_reference_file ]]; then
        log_error "Attempting backup to soon after previous backup"

        exit 1
    fi
fi


if ! mountpoint -q $backup_mount; then
    mount_backup_device
fi


log "Creating backup"

borg create                     \
    --warning                   \
    --filter E                  \
    --compression lz4           \
    --exclude-from $exclude_file    \
    --exclude-caches            \
                                \
    ::'pascal_desktop-{now}'    \
    / 2>&1 | timestamp

backup_exit=$?


log "Pruning borg repository"

borg prune                      \
    --warning                   \
    --prefix 'pascal_desktop-'  \
    --keep-daily    7           \
    --keep-weekly   4           \
    --keep-monthly  12          \
    2>&1 | timestamp

prune_exit=$?


borg_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [[ $borg_exit -gt 0 ]]; then
    log_error "Borg exited with non-zero exit code $borg_exit"
    exit 3
fi

exit 0
