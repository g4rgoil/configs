#!/bin/bash

slack_url="https://hooks.slack.com/services/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"
tformat="%Y-%m-%d %H:%M:%S"

script_directory="/etc/backup_scripts"
# script_file="${script_directory}/desktop_backup.sh"
exclude_file="${script_directory}/root.exclude"

log_directory="/var/log/backup_logs"
log_file="${log_directory}/root.log"

spool_directory="/var/spool/backups"
spool_ts_file="${spool_directory}/desktop_ts"

min_backup_interval="-6 hours"
time_reference_file=$(mktemp)

backup_mount="/hdd/mybook"
backup_repo="${backup_mount}/Borg_Backups/pascal_desktop"
unmount=false

export BORG_REPO=$backup_repo
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/mybook_desktop"


function slack_message() {
    curl -X POST --data-urlencode "payload={'text': '$(hostname): ${1}'}" \
        $slack_url >/dev/null 2>&1
}

function timestamp() {
    ts "[${tformat}]" >> $log_file
}

function log() {
    echo -e "$1" | timestamp
}

function log_error() {
    log "ERROR: $1"
}

function blank_line() {
    echo "" >> $log_file
}

function unmount_backup_device() {
    if [[ "$unmount" = true ]]; then
        log "Unmounting backup device"
        unmount $backup_mount
    fi
}

function finish() {
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        date +%Y%m%d%H%M > $spool_ts_file
    fi

    unmount_backup_device
    
    log "Finishing backup procedure"
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


if [[ ! -d $log_directory ]]; then
    log "Creating backup log directory"
    mkdir -p $log_directory
fi

if [[ ! -d $spool_directory ]]; then
    log "Creating spool directory"
    mkdir -p $spool_directory
fi

if [[ ! -d $backup_mount ]]; then
    log "Creating mount point for backup device"
    mkdir -p $backup_mount
fi


log "Starting backup procedure"


if [[ -f $spool_ts_file ]]; then
    touch -t "$(<$spool_ts_file)" $spool_ts_file
    touch -d "$min_backup_interval" "$time_reference_file"

    if [[ $spool_ts_file -nt $time_reference_file ]]; then
        log_error "Attempting backup to soon after previous backup"

        exit 1
    fi
fi


if ! mountpoint -q $backup_mount; then
    log "Mounting backup device"

    if ! mount $backup_mount || ! mountpoint -q $backup_mount; then
        log_error "Unable to mount backup device"
        slack_message "$(hostname): Backup failed, unable to mount backup target."
        exit 2
    fi

    unmount=true
fi



if [[ ! -d "${backup_repo}" ]]; then
    log_error "Borg repository doesn't exist"
    slack_message "$(hostname): Backup failed, borg repository doesn't exist."
    exit 2
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
