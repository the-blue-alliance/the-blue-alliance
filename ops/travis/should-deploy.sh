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
    endpoints_sha=$(sha1sum tbaMobilev9openapi.json | awk '{ echo $1 }')
    tbaClient_endpoints_sha=$(sha1sum tbaClientv9openapi.json | awk '{ echo $1 }')

    http $SET_BUILD_STATUS X-TBA-Auth-Key:$APIv3_KEY current_commit="$current_commit" commit_time="$commit_time" deploy_time="$deploy_time" travis_job="$travis_job" endpoints_sha="$endpoints_sha" tbaClient_endpoints_sha="$tbaClient_endpoints_sha"
}

check_killswitch() {
    enabled=$(fetch_apiv3_status | jq '.contbuild_enabled')
    if [ "$enabled" != "true" ]; then
        echo "Continuous Deployment disabled via killswitch..."
        exit 0
    fi
}

check_overwrite_old() {
    echo "Pulling currently deployed commit..."
    web_status=$(fetch_apiv3_status | jq '.web')
    commit=$(echo $web_status | jq '.current_commit')
    prod_time_str=$(echo $web_status | jq '.commit_time')
    local_time_str=$(git show -s --format=%ci HEAD)

    echo "Prod is currently running $commit, committed at $prod_time_str"
    echo "Current commit was committed at $local_time_str"

    # Convert time strings to UNIX time
    prod_time=$(echo $prod_time_str | date +%s)
    local_time=$(echo $local_time_str | date +%s)
    msg=$(git log -1 --pretty=%B)
    if [ "$local_time" -lt "$prod_time" ]; then
        case "$msg" in
            *\[clowntown\]*) echo "Commit is older, but [clowntown] found. Be careful..." ;;
	    *) echo "Not overwriting prod with an older commit, exiting..."; exit 0 ;;
	esac
    fi
}

check_deploy_endpoints_config() {
    endpoints_sha=$(sha1sum tbaMobilev9openapi.json | awk '{ echo $1 }')

    echo "Pulling deployed endpoints sha..."
    web_status=$(fetch_apiv3_status | jq '.web')
    deployed_sha=$(echo $web_status | jq '.endpoints_sha')

    echo "Previously deployed endpoints sha is $deployed_sha"
    echo "New endpoints sha is $endpoints_sha"

    if [ "$deployed_sha" -eq "$endpoints_sha" ]; then
        echo "Deployed endpoints sha is the same as current endpoints sha. No need to deploy."
        exit 0
    fi
}

check_deploy_tbaClient_endpoints_config() {
    endpoints_sha=$(sha1sum tbaClientv9openapi.json | awk '{ echo $1 }')

    echo "Pulling deployed tbaClient endpoints sha..."
    web_status=$(fetch_apiv3_status | jq '.web')
    deployed_sha=$(echo $web_status | jq '.endpoints_sha')

    echo "Previously deployed tbaClient endpoints sha is $deployed_sha"
    echo "New tbaClient endpoints sha is $endpoints_sha"

    if [ "$deployed_sha" -eq "$endpoints_sha" ]; then
        echo "Deployed tbaClient endpoints sha is the same as current endpoints sha. No need to deploy."
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
    check_overwrite_old
}
