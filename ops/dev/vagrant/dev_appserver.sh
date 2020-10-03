#! /bin/bash
set -e

function get_config_prop {
    local prop_name="$1"
    local dev_config_file=""
    if [ -f "tba_dev_config.local.json" ]; then
        local dev_config_file="tba_dev_config.local.json"
    fi

    jq -r -s ".[0] * (.[1] // {}) | .$prop_name | select (.!=null)" tba_dev_config.json $dev_config_file
}

function get_project_from_key {
    local key_path="$1"
    jq -r '.project_id' "$key_path"
}

log_level=$(get_config_prop log_level)
tba_log_level=$(get_config_prop tba_log_level)
ndb_log_level=$(get_config_prop ndb_log_level)
datastore_mode=$(get_config_prop datastore_mode)
datastore_args=""
application=""
env=""

# Setup Google Application Credentials, if available
google_application_credentials=$(get_config_prop google_application_credentials)
if [ $google_application_credentials ]; then
    cred_file=$(realpath $google_application_credentials)
    project=$(get_project_from_key "$cred_file")
    application="--application $project"
    env="$env --env_var GOOGLE_APPLICATION_CREDENTIALS=$cred_file"
else
    application="--application test"
fi

function assert_google_application_credentials {
    if [ -z $google_application_credentials ]; then
        echo "google_application_credentials required to be set in tba_dev_config"
        exit -1
    fi
}

# Setup Cloud Datastore emulator/remote
if [ "$datastore_mode" == "local" ]; then
    echo "Starting with datastore emulator"
    emulator_port=8089
    datastore_path="/datastore/tba.db"
    datastore_args="--support_datastore_emulator=true --datastore_emulator_port=$emulator_port --datastore_path=$datastore_path"
    env="$env --env_var DATASTORE_EMULATOR_HOST=localhost:$emulator_port --env_var DATASTORE_DATASET=test"
elif [ "$datastore_mode" == "remote" ]; then
    echo "Starting with remote datastore"
    assert_google_application_credentials
else
    echo "Unknown datastore mode $datastore_mode! Must be one of [local, remote]"
    exit -1
fi

set -x
dev_appserver.py \
    --admin_host=0.0.0.0 \
    --host=0.0.0.0 \
    $application \
    $datastore_args \
    $env \
    --env_var TBA_LOG_LEVEL="$tba_log_level" \
    --env_var NDB_LOG_LEVEL="$ndb_log_level" \
    --dev_appserver_log_level=$log_level \
    src/default.yaml src/web.yaml src/api.yaml src/tasks_io.yaml src/dispatch.yaml
