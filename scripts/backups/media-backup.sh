#!/bin/bash

script_directory="/usr/lib/backup-scripts"
library_file="${script_directory}/backup-library.sh"

# shellcheck source=/usr/lib/backup-scripts/backup-library.sh
source ${library_file}

# script_file="${script_directory}/media-backup.sh"
pattern_file="${script_directory}/media.pattern"

log_directory="/var/log/backups"
ts_file="${log_directory}/media.ts"
log_file="${log_directory}/media.log"

pid_file="/var/run/media-backup.pid"

interval="-12 hours"

backup_dst="/hdd/mybook"
backup_src="/hdd/media"
unmount_src=""
unmount_dst=""

export BORG_REPO="${backup_dst}/borg/pascal_media"
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/mybook_media"

function unmount_backup_devices() {
    if ensure_unmounted ${backup_src} ${unmount_src}; then
        unmount_src=""
    fi

    if ensure_unmounted ${backup_dst} ${unmount_dst}; then
        unmount_dst=""
    fi
}

function finish() {
    exit_code=$?

    unmount_backup_devices

    if [[ ${exit_code} -eq 0 ]]; then
        set_timestamp ${ts_file}
        log "Finishing backup procedure"
    else
        log "Backup procedure failed with exit code $exit_code"
    fi

    blank_line
    exit ${exit_code}
}

function terminate() {
    log_error "The backup procedure was interrupted by a signal"

    unmount_backup_devices

    blank_line
    exit ${interrupt_exit}
}

trap finish EXIT

trap 'trap "" EXIT; terminate' \
    HUP INT QUIT TERM


log "Starting backup procedure"

if ! require_root; then
    exit ${permission_error}
fi

if ! require_single_instance ${pid_file}; then
    exit ${multiple_instance_exit}
fi

require_directory ${log_directory} "log directory"
require_directory ${backup_dst} "mount point for backup device"

if ! require_backup_interval ${ts_file} "$interval"; then
    exit ${insufficient_interval_exit}
fi

if ! ensure_mounted ${backup_src} unmount_src; then
    exit ${mount_exit}
fi

if ! ensure_mounted ${backup_dst} unmount_dst; then
    exit ${mount_exit}
fi

create_backup ${backup_src} "pascal_media" "lz4"
backup_exit=$?

prune_repository "pascal_media"
prune_exit=$?

borg_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [[ ${borg_exit} -gt 0 ]]; then
    log_error "Borg exited with non-zero exit code $borg_exit"
    exit ${borg_exit}
fi

exit 0
