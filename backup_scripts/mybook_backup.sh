#!/bin/bash

slack_url="https://hooks.slack.com/services/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"
tformat="%Y-%m-%d %H:%M:%S"

script_directory="/etc/backup_scripts"
script_file="${script_directory}/xps13_backup.sh"
exclude_file="${script_directory}/mybook.exclude"

log_directory="/var/log/backup_logs"
ts_file="${log_directory}/mybook.ts"
log_file="${log_directory}/mybook.log"
job_file="${log_directory}/mybook.job"

pid_file="/var/run/xps13-backup.pid"

min_backup_interval="-24 hours"
time_reference_file=$(mktemp)

backup_src="/hdd/mybook"
unmount=false

ssh_user="pascal"
ssh_host="192.168.3.47"

export BORG_REPO="ssh://${ssh_user}@${ssh_host}/pool/pascal/borg-repository"
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/zfsnas_mybook"

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

function mount_backup_device() {
    log "Mounting mybook"

    if ! mount $backup_src || ! mountpoint -q $backup_src; then
        log_error "Unable to mount mybook"
        slack_message "Backup failed, unable to mount mybook."
        exit 2
    fi

    unmount=true
}

function unmount_backup_device() {
    if [[ "$unmount" = true ]]; then
        log "Unmounting backup device"
        umount $backup_src
    fi

    umount=false
}

function remove_scheduling() {
    if [[ -f "$job_file" ]]; then
        job_id=$(<$job_file)
        at -r "$job_id" >/dev/null 2>&1
        rm "$job_file" >/dev/null 2>&1
    fi
}

function add_scheduling() {
    echo "/bin/bash $script_file" | \
        at now + 4 hour 2>&1 |      \
        tail -1 |                   \
        cut -f2 -d" " >             \
        $job_file
}


function finish() {
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        date +%Y%m%d%H%M > $ts_file
    fi
    
    log "Finishing backup procedure"
    slack_message "Finished weekly mybook backup"
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

if [[ ! -d $backup_src ]]; then
    log "Creating mount point for mybook"
    mkdir -p $backup_src
fi

remove_scheduling

log "Starting backup procedure"
slack_message "Starting weekly mybook backup"


if [[ -f $ts_file ]]; then
    touch -t "$(<$ts_file)" $ts_file
    touch -d "$min_backup_interval" "$time_reference_file"

    if [[ $ts_file -nt $time_reference_file ]]; then
        log_error "Attempting backup to soon after previous backup"

        exit 1
    fi
fi


if ! ping -c 1 $ssh_host >/dev/null 2>&1; then
    log_error "Unable to communicate with ssh server"
    log "Scheduling backup to be rerun later"

    slack_message "Backup failed, unable to communicate with ssh server"
    slack_message "Scheduling backup to be rerun"

    add_scheduling
    exit 2
fi


if ! mountpoint -q $backup_src; then
    mount_backup_device
fi


log "Creating backup"


borg create                 \
    --warning               \
    --filter E              \
    --compression zlib,5    \
    --exclude-from $exclude_file    \
    --exclude-caches        \
                            \
    ::'mybook-{now}'        \
    ${backup_src}           \
    2>&1 | timestamp

backup_exit=$?


log "Pruning borg repository"

borg prune                  \
    --warning               \
    --prefix 'mybook-'      \
    --keep-daily    7       \
    --keep-weekly   4       \
    --keep-monthly  12      \
    2>&1 | timestamp

prune_exit=$?


borg_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [[ $borg_exit -gt 0 ]]; then
    log_error "Borg exited with non-zero exit code $borg_exit"
    exit 3
fi

exit 0
