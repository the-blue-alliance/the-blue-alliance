## Pre-Kickoff

Each year, we've been generating "team media admin" keys to be distributed in the KOP. We generate one randomly for each team number, and then import them to TBA.

To generate:

```python
#! /usr/bin/env python3

import argparse
import csv
import random
import string

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile')
    parser.add_argument("--length", default=15)
    args = parser.parse_args()

    with open(args.outfile, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Team Number", "TBA Key"])
        for team_num in range(1, 10000):
            key = "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=args.length))
            writer.writerow([team_num, key])

if __name__ == "__main__":
    main()
```

After generating the keys, email them to the POC at HQ to be included in the KOP distribution.

To import, use [this Admin panel page](https://www.thebluealliance.com/admin/media/modcodes/add).

Sometimes, the request to add them will OOM if you try to import too many, so split them into smaller batches.

```bash
# the `tail` call will skip the header row added by the script above
$ cat tba_keys.csv | tail -n +2 | head -n 10 | split -l 1000
```

## Kickoff

The [landing page config](https://www.thebluealliance.com/admin/main_landing) and the [GameDay config](https://www.thebluealliance.com/admin/gameday) can be used for most of the Kickoff-related tasks.

Before kickoff, set the landing page type to be `Kickoff`. A `kickoff_facebook_fbid` and `game_teaser_youtube_id` can be configured in the landing page config to show a game teaser video, as well as link to a Facebook event for Kickoff. The page will update with a link to the GameDay `/watch/kickoff` link automatically once Kickoff is within the next 24 hours. Ensure there is a `kickoff` URL alias in the GameDay config URL aliases that auto-plays the `firstinspires` stream.

Once the game is announced, the landing page type should be changed to `Build Season`. Update the `game_animation_youtube_id`, `game_name`, `manual_password`, and `build_handler_show_password` properties accordingly. To show a button to link to Robot in 3 Days streams in GameDay, set the `build_handler_show_ri3d` to be `True`. Ensure there is a `ri3d` URL alias in the GameDay config URL aliases that auto-plays the Ri3D streams.
