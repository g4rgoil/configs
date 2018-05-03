#!/bin/bash

script_directory="/etc/backup_scripts"
library_file="${script_directory}/backup_library.sh"

# shellcheck source=/dev/null
source $library_file

# script_file="${script_directory}/desktop_backup.sh"
exclude_file="${script_directory}/root.exclude"

log_directory="/var/log/backup_logs"
ts_file="${log_directory}/desktop.ts"
log_file="${log_directory}/root.log"

pid_file="/var/run/desktop-backup.pid"

backup_dst="/hdd/mybook"
backup_src="/"
unmount_dst=false

export BORG_REPO="${backup_dst}/Borg_Backups/pascal_desktop"
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/mybook_desktop"

function finish() {
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        set_timestamp
    fi

    if [[ "$unmount_dst" = true ]]; then
        unmount_device $backup_dst
        unmount_dst=false
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        log "Finishing backup procedure"
    else
        log "Backup procedure failed with exit code $exit_code"
    fi

    blank_line
}

function terminate() {
    log_error "The backup procedure was interrupted by a signal"

    if [[ "$unmount_dst" = true ]]; then
        unmount_device $backup_dst
        unmount_dst=false
    fi

    blank_line
}

trap finish EXIT

trap 'trap "" EXIT; terminate' \
    HUP INT QUIT TERM


require_single_instance

require_directory $log_directory "log directory"
require_directory $backup_dst "mount point for backup device"


log "Starting backup procedure"

require_backup_interval

if ! mountpoint -q $backup_dst; then
    mount_device $backup_dst
    unmount_dst=true
fi


create_backup "pascal_desktop" "lz4"
backup_exit=$?

prune_repository "pascal_desktop"
prune_exit=$?

borg_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [[ $borg_exit -gt 0 ]]; then
    log_error "Borg exited with non-zero exit code $borg_exit"
    exit 3
fi

exit 0
