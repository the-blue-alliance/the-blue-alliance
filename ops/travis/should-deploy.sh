#! /usr/bin/env sh

API_STATUS=https://www.thebluealliance.com/api/v3/status
fetch_apiv3_status() {
    curl -s --header "X-TBA-Auth-Key: $APIv3_KEY" $API_STATUS
}

check_killswitch() {
    enabled=$(fetch_apiv3_status | jq '.contbuild_enabled')
    if [ "$enabled" != "true" ]; then
        echo "Continuous Deployment disabled via killswitch..."
        exit 0
    fi
}

check_commit_tag() {
    # The most recent commit message
    msg=$(git log -1 --pretty=%B)
    case "$msg" in
        *\[nodeploy\]*) echo "Skipping due to [nodeploy] tag"; exit 0 ;;
    esac
}

should_deploy() {
    check_commit_tag
    check_killswitch
}
