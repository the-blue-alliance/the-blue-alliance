#! /bin/bash
set -e

source ops/dev/vagrant/config.sh

auth_use_prod=$(get_config_prop auth_use_prod)
log_level=$(get_config_prop log_level)
tba_log_level=$(get_config_prop tba_log_level)
ndb_log_level=$(get_config_prop ndb_log_level)
datastore_mode=$(get_config_prop datastore_mode)
redis_cache_url=$(get_config_prop redis_cache_url)
tasks_mode=$(get_config_prop tasks_mode)
tasks_remote_config_ngrok_url=$(get_config_prop tasks_remote_config.ngrok_url)
flask_response_cache_enabled=$(get_config_prop flask_response_cache_enabled)
storage_mode=$(get_config_prop storage_mode)
storage_path=$(get_config_prop storage_path)
application=""
tasks_args=()
env=()

# Setup Google Application Credentials, if available
google_application_credentials=$(get_config_prop google_application_credentials)
if [ "$google_application_credentials" ]; then
    cred_file=$(realpath "$google_application_credentials")
    project=$(get_project_from_key "$cred_file")
    application="$project"
    env+=("--env_var=GOOGLE_APPLICATION_CREDENTIALS=$cred_file")
else
    application="test"
fi

function assert_google_application_credentials {
    if [ -z "$google_application_credentials" ]; then
        echo "google_application_credentials required to be set in tba_dev_config"
        exit 1
    fi
}

function assert_tasks_remote_config_ngrok_url {
    if [ -z "$tasks_remote_config_ngrok_url" ]; then
        echo "tasks_remote_config.ngrok_url required to be set in tba_dev_config"
        exit 1
    fi
}

function assert_local_storage_path {
    if [ -z "$storage_path" ]; then
        echo "storage_path required to be set in tba_dev_config when using local storage mode"
        exit 1
    fi
}

# Setup Cloud Datastore emulator/remote
if [ "$datastore_mode" == "local" ]; then
    echo "Starting with datastore emulator"
    emulator_port=8089
    env+=("--env_var=DATASTORE_EMULATOR_HOST=localhost:$emulator_port" "--env_var=DATASTORE_DATASET=test")
elif [ "$datastore_mode" == "remote" ]; then
    echo "Starting with remote datastore"
    assert_google_application_credentials
else
    echo "Unknown datastore mode $datastore_mode! Must be one of [local, remote]"
    exit 1
fi

# Set up Cloud Datastore global redis cache
if [ -z "$redis_cache_url" ]; then
    echo "Running without redis cache"
else
    echo "Starting with redis cache at $redis_cache_url"
    env+=("--env_var=REDIS_CACHE_URL=$redis_cache_url")
fi

# Setup Google Cloud Tasks local/remote
if [ "$tasks_mode" == "local" ]; then
    echo "Using local tasks (rq + Redis)"
elif [ "$tasks_mode" == "remote" ]; then
    echo "Using remote tasks (Cloud Tasks + ngrok)"
    assert_google_application_credentials
    assert_tasks_remote_config_ngrok_url
    # Need to disable host checking to allow for round-trip requests coming from ngrok
    tasks_args=("--enable_host_checking=false")
    env+=("--env_var=TASKS_REMOTE_CONFIG_NGROK_URL=$tasks_remote_config_ngrok_url")
else
    echo "Unknown tasks mode $tasks_mode! Must be one of [local, remote]"
    exit 1
fi

# Setup Cloud Storage local/remote
if [ "$storage_mode" == "local" ]; then
    echo "Starting with local storage"
    assert_local_storage_path
    storage_path=$(realpath "$storage_path")
    env+=("--env_var=STORAGE_PATH=$storage_path")
elif [ "$storage_mode" == "remote" ]; then
    echo "Starting with remote storage for $project"
    assert_google_application_credentials
else
    echo "Unknown storage mode $storage_mode! Must be one of [local, remote]"
    exit 1
fi

# Setup Firebase auth emulator
if [ -z "$auth_use_prod" ]; then
    echo "Running with Firebase auth emulator"
    env+=("--env_var=FIREBASE_AUTH_EMULATOR_HOST=localhost:9099")
else
    echo "Using upstream authentication accounts"
    assert_google_application_credentials
fi

set -x
dev_appserver.py \
    --runtime_python_path=/usr/bin/python3 \
    --admin_host=0.0.0.0 \
    --host=0.0.0.0 \
    --runtime="python37" \
    --application="$application" \
    "${tasks_args[@]}" \
    "${env[@]}" \
    --env_var TBA_LOG_LEVEL="$tba_log_level" \
    --env_var NDB_LOG_LEVEL="$ndb_log_level" \
    --env_var TASKS_MODE="$tasks_mode" \
    --env_var STORAGE_MODE="$storage_mode" \
    --env_var FLASK_RESPONE_CACHE_ENABLED="$flask_response_cache_enabled" \
    --env_var GCLOUD_PROJECT="$application" \
    --dev_appserver_log_level="$log_level" \
    src/default.yaml src/web.yaml src/api.yaml src/tasks_io.yaml src/dispatch.yaml
