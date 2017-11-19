#! /usr/bin/env sh

API_STATUS=https://www.thebluealliance.com/api/v3/status
SET_BUILD_STATUS=https://www.thebluealliance.com/api/v3/_/build
fetch_apiv3_status() {
    curl -s --header "X-TBA-Auth-Key: $APIv3_KEY" $API_STATUS
}

update_build_info() {
    current_commit=$TRAVIS_COMMIT
    commit_time="$(git show -s --format=%ci HEAD)"
    deploy_time="$(date)"
    travis_job="$TRAVIS_BUILD_ID"

    http $SET_BUILD_STATUS x-TBA-Auth-Key:$APIv3_KEY current_commit="$current_commit" commit_time="$commit_time" deploy_time="$deploy_time" travis_job="$travis_job"
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

check_clowntown_tag() {
    # Don't allow for non-pull requests
    if test "$TRAVIS_PULL_REQUEST" != "false" ; then
        return
    fi

    # The most recent commit message
    msg=$(git log -1 --pretty=%B)
    case "$msg" in
        *\[clowntown\]*) echo "Skipping due to [clowntown] tag. You better know what you're doing..."; exit 0 ;;
    esac
}

should_deploy() {
    check_commit_tag
    check_killswitch
}
