#!/bin/bash

slack_url="https://hooks.slack.com/services/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"
tformat="%Y-%m-%d %H:%M:%S"

log_file=""

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
