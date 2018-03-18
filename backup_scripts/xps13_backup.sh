#!/bin/bash

slack_url="https://hooks.slack.com/services/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"
tformat="%Y-%m-%d %H:%M:%S"

script_directory="/etc/backup_scripts"
script_file="${script_directory}/xps13_backup.sh"
exclude_file="${script_directory}/root.exclude"

log_directory="/var/log/backup_logs"
log_file="${log_directory}/root.log"

spool_directory="/var/spool/backups"
spool_job_file="${spool_directory}/xps13_job"
spool_ts_file="${spool_directory}/xps13_ts"

min_backup_interval="-6 hours"
time_reference_file=$(mktemp)

ssh_user="root"
ssh_host="pascal_desktop"

export BORG_REPO="ssh://${ssh_user}@${ssh_host}/hdd/mybook/Borg_Backups/pascal_xps13"
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/mybook_xps13"


function slack_message() {
    curl -X POST --data-urlencode "payload={'text': '$(hostname): ${1}'}" \
        $slack_url >/dev/null 2>&1
}

function timestamp() {
    ts "[${tformat}]" >> $log_file
}

function log() {
    echo "$1" | timestamp
}

function log_error() {
    log "ERROR: $1"
}


function remove_scheduling() {
    if [[ -f "$spool_job_file" ]]; then
        job_id=$(<$spool_job_file)
        at -r "$job_id" >/dev/null 2>&1
        rm "$spool_job_file" >/dev/null 2>&1
    fi
}

function add_scheduling() {
    remove_scheduling

    mkdir -p "$spool_directory"
    echo "/bin/bash $script_file" | \
        at now + 1 hour 2>&1 |      \
        tail -1 |                   \
        cut -f2 -d" " >             \
        $spool_job_file
}


function finish() {
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        date +%Y%m%d%H%M > $spool_ts_file
    fi
    
    log "Finishing backup procedure"
    log ""
}

trap finish EXIT

trap 'trap "" EXIT; log_error "The backup was interrupted by a signal\n"' \
    HUP INT QUIT TERM


if [[ ! -d $log_directory ]]; then
    log "Creating backup log directory"
    mkdir -p $log_directory
fi

if [[ ! -d $spool_directory ]]; then
    log "Creating spool directory"
    mkdir -p $spool_directory
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


if ! ping -c 1 $ssh_host >/dev/null 2>&1; then
    log_error "Unable to communicate with ssh server"
    log "Scheduling backup to be rerun later"

    slack_message "$(hostname): Backup failed, unable to communicate with ssh server. Scheduling backup to be rerun."

    add_scheduling
    exit 2
fi

remove_scheduling


log "Creating backup"


borg create                     \
    --warning                   \
    --filter E                  \
    --compression lz4           \
    --exclude-from $exclude_file    \
    --exclude-caches            \
                                \
    ::'pascal_xps13-{now}'      \
    / 2>&1 | timestamp

backup_exit=$?


log "Pruning borg repository"

borg prune                      \
    --warning                   \
    --prefix 'pascal_xps13-'    \
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
