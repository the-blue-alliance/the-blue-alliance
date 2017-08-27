#! /usr/bin/env sh

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
