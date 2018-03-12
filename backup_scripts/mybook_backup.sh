#!/bin/bash

slack_url="https://hooks.slack.com/services/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"
script_directory="/etc/backup_scripts"
log_directory="/var/log/backup_logs"
log="$log_directory/mybook.log"
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

ssh_user="pascal"
ssh_host="192.168.3.47"

if ! ping -c 1 "${ssh_host}" >/dev/null 2>&1; then
    log_error "Unable to communicate with ssh server"
    slack_message "$(hostname):" \
        "Backup failed, unable to communicate with ssh server"
    exit 2
fi


backup_src="/hdd/mybook"

if [[ ! -d ${backup_src} ]]; then
    log "Creating mount point for mybook"
    mkdir -p ${backup_src}
fi

unmount=false

if ! mountpoint -q ${backup_src}; then
    log "Mounting mybook"

    if ! mount ${backup_src} || ! mountpoint -q ${backup_src}; then
        log_error "Unable to mount mybook"
        slack_message "$(hostname): Backup failed, unable to mount mybook."
        exit 2
    fi

    unmount=true
fi


export BORG_REPO="ssh://${ssh_user}@${ssh_host}/pool/pascal/borg-repository"
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/zfsnas_mybook"

log "Creating backup"

exclude_file="${script_directory}/mybook.exclude"

borg create                 \
    --warning               \
    --stats                 \
    --list                  \
    --filter E              \
    --stats                 \
    --compression zlib,5    \
    --exclude-from ${exclude_file}  \
                            \
    ::'mybook-{now}'        \
    ${backup_src}           \
    2>&1 | ts "[${tformat}]" >> $log

backup_exit=$?


log "Pruning borg repository"

borg prune                  \
    --list                  \
    --prefix 'mybook-'      \
    --keep-daily    7       \
    --keep-weekly   4       \
    --keep-monthly  12      \
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
    umount ${backup_src}
fi

log "Finishing backup procedure"
echo "" >> $log

exit ${global_exit}
