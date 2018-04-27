#! /usr/bin/env sh

# Hit a bunch of pages on the site and make sure nothing errors
# Takes the bas TBA url as $1

tba_base=$1

declare -a endpoints=("/"
                      "/events"
                      "/event/2017cthar"
                      "/event/2017nyny"
                      "/event/2017arc"
                      "/event/2017cmp"
                      "/event/2018cthar"
                      "/event/2018nyny"
                      "/teams"
                      "/team/254"
                      "/team/254/2017"
                      "/team/254/2018"
                      "/team/254/history"
                      )

echo "Running simple smoke tests on $tba_base"
timestamp=$(date +%s)
for endpoint in "${endpoints[@]}"; do
  printf "Checking endpoint ${endpoint}..."
  # Append the current timestamp to bust edge cache
  url="${tba_base}${endpoints}?${timestamp}"
  ret=$(curl -s -o /tmp/tbaout -w "%{http_code}" "$url")
  if [ "$ret" != "200" ]; then
    printf "\nRequesting ${tba_base}${endpoint} failed with code $ret\n"
    cat /tmp/tbaout
    exit -1
  else
    rm -f /tmp/tbaout
    echo "OK"
  fi
done
