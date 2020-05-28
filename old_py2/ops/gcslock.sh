#!/bin/sh
#
# From: https://github.com/marcacohen/gcslock
#
# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This file illustrates how to the use the gcslock global mutex
# via the gsutil command in a shell script. It depends on installation
# of the Google Cloud SDK (https://cloud.google.com/sdk/), which
# includes the gsutil command.
#
# Usage example:
#
#	source gcslock.sh
# 	lock mybucket
# 	echo "lock acquired"
# 	unlock mybucket

# The lock function expects the first (and only) argument to be
# the name of a bucket writable by the user running this script.
# It creates the lock object in the passed bucket with a special
# header to obtain mutual exclusion. If the lock object creation
# fails, it retries indefinitely with expontential backoff.

lock() {
  if [ "$1" = "" ]
  then
    echo "lock: missing bucket argument"
    exit 1
  fi
  LOCK="gs://$1/lock"
  sleep_time=1
  while ! echo "lock" | gsutil -q -h "x-goog-if-generation-match:0" cp - $LOCK
  do
    echo "lock: failed to obtain lock, retrying in $sleep_time seconds"
    sleep $sleep_time
    sleep_time=$(expr $sleep_time '*' 2)
  done
}

# The unlock function expects the first (and only) argument to be
# the name of a bucket writable by the user running this script.
# It relinquishes the lock by removing the lock object. If the
# lock object removal fails, it retries indefinitely with
# expontential backoff.

unlock() {
  if [ "$1" = "" ]
  then
    echo "unlock: missing bucket argument"
    exit 1
  fi
  LOCK="gs://$1/lock"
  sleep_time=1
  while ! gsutil -q rm $LOCK
  do
    echo "unlock: failed to relinquish lock, retrying in $sleep_time seconds"
    sleep $sleep_time
    sleep_time=$(expr $sleep_time '*' 2)
  done
}

