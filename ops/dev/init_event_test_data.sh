#! /bin/bash

set -euo pipefail

source ops/dev/vagrant/config.sh

API_URL="https://www.thebluealliance.com/api/v3"
APIV3_KEY=$(get_config_prop apiv3_key)
EVENT_KEY="$1"
DATA_DIR="$2"

function fetch_endpoint {
    local event_key="$1"
    local endpoint_suffix="$2"
    if [ -z "$endpoint_suffix" ]; then
        local url_path="$API_URL/event/$event_key"
        local output_file="$DATA_DIR/${event_key}.json"
    else
        local url_path="$API_URL/event/$event_key/$endpoint_suffix"
        local output_file="$DATA_DIR/${event_key}_${endpoint_suffix}.json"
    fi

    curl -o "$output_file" -H "X-TBA-Auth-Key:$APIV3_KEY" "$url_path"
}

if [ -z "$APIV3_KEY" ]; then
    echo "No apiv3_key found in tba_dev_config.local.json!"
    exit 0
fi

if [ ! -d "$DATA_DIR" ]; then
    echo "Directory $DATA_DIR does not exist"
    exit 0
fi

fetch_endpoint "$EVENT_KEY" ""
fetch_endpoint "$EVENT_KEY" "matches"
fetch_endpoint "$EVENT_KEY" "alliances"
fetch_endpoint "$EVENT_KEY" "teams"
fetch_endpoint "$EVENT_KEY" "rankings"
fetch_endpoint "$EVENT_KEY" "awards"
fetch_endpoint "$EVENT_KEY" "district_points"
fetch_endpoint "$EVENT_KEY" "regional_champs_pool_points"
