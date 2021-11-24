#!/usr/bin/env python
import sys
import time

import requests

TIME_LIMIT = 10 * 60  # seconds

start_time = time.time()
while time.time() - start_time < TIME_LIMIT:
    try:
        url = "http://localhost:8080"
        r = requests.get(url)
        if r.status_code == 200:
            if "The Blue Alliance" in r.text:
                print("Success!")
                sys.exit(0)
            else:
                print("Fail: 200 with unexpected content")
                sys.exit(1)
    except Exception as e:
        print(e)
    time.sleep(5)

print("Fail: Timeout")
sys.exit(1)
