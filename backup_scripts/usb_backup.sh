#!/bin/bash

script_directory="/etc/backup_scripts"
library_file="${script_directory}/backup_library.sh"

# shellcheck source=/etc/backup_scripts/backup_library.sh
source $library_file

exclude_file="${script_directory}/usb.exclude"

log_directory="/var/log/backup_logs"
log_file="${log_directory}/usb.log"

backup_dst="/hdd/mybook"
prefix="${1:-unkown}"
backup_src="${2:-/mnt/usb}"
unmount_dst=false

export BORG_REPO="${backup_dst}/Borg_Backups/pascal_usb"
export BORG_KEY_FILE="/root/.config/borg/keys/mybook_usb"  # TODO

function finish() {
    exit_code=$?

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


require_directory $log_directory "log directory"
require_directory $backup_dst "mount point for backup device"


log "Starting backup procedure"

if ! mountpoint -q $backup_dst; then
    if ! mount_device $backup_dst; then
        exit $mount_exit
    fi

    unmount_dst=true
fi

password=""
require_password "Enter BORG password" password
export BORG_PASSPHRASE="$password"

create_backup "$backup_src" "$prefix" "lz4"
backup_exit=$?

prune_repository "$prefix"
prune_exit=$?

borg_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [[ $borg_exit -gt 0 ]]; then
    log_error "Borg exited with non-zero exit code $borg_exit"
    exit $borg_exit
fi

exit 0
