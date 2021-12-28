#! /bin/bash
function get_config_prop {
    local prop_name="$1"
    local dev_config_file=""
    if [ -f "tba_dev_config.local.json" ]; then
        local dev_config_file="tba_dev_config.local.json"
    fi

    jq -c -r -s ".[0] * (.[1] // {}) | .$prop_name | select (.!=null)" tba_dev_config.json $dev_config_file
}

function get_project_from_key {
    local key_path="$1"
    jq -r '.project_id' "$key_path"
}

function project {
    # Setup Google Application Credentials, if available
    google_application_credentials=$(get_config_prop google_application_credentials)
    if [ "$google_application_credentials" ]; then
        cred_file=$(realpath "$google_application_credentials")
        project=$(get_project_from_key "$cred_file")
        echo "$project"
    else
        echo "test"
    fi
}
