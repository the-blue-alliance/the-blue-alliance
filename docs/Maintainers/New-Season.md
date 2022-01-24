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

## During Build

### Avatars

TODO

## Pre-First Event

### Match Breakdowns JSON

The match breakdown JSON format should be communicated from FIRST before the first event happens either via email or [from the API documentation](https://frc-api-docs.firstinspires.org). Once we know the format-

* Add the API breakdown keys to [score_breakdown_keys.py](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/helpers/score_breakdown_keys.py) to support parsing from the FRC API ([2022 Example](https://github.com/the-blue-alliance/the-blue-alliance/pull/4195))
* Add a new [match_breakdown_{year}.html](https://github.com/the-blue-alliance/the-blue-alliance/tree/py3/src/backend/web/templates/match_partials/match_breakdown) page to show match breakdowns on the match page ([2022 Example](https://github.com/the-blue-alliance/the-blue-alliance/pull/4195/files#diff-a8a491e43dc48c7848f2217aef3814b32f2de6dacd35e7180028b4f7574b5c31))
* Update the [`swagger/api_v3.json`](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/web/static/swagger/api_v3.json) with new `Match_Score_Breakdown_{year}` and `Match_Score_Breakdown_{year}_Alliance` models ([2022 Example](https://github.com/the-blue-alliance/the-blue-alliance/pull/4195/files#diff-47a7c4cba3cd134ecf1af29f5fe3fdf79f03b58e2661a89c21eb8e6b42f7744b))
* Optionally, [Match.score_breakdown](https://github.com/the-blue-alliance/the-blue-alliance/blob/07912c3d278c102d9bc58da3cb0e78baf5d9a8ba/src/backend/common/models/match.py#L195) (and possibly [fms_api_match_parser.py](https://github.com/the-blue-alliance/the-blue-alliance/blob/07912c3d278c102d9bc58da3cb0e78baf5d9a8ba/src/backend/tasks_io/datafeeds/parsers/fms_api/fms_api_match_parser.py#L368-L389), but probably not) if there need to be any TBA-derived fields on the match breakdown JSON

Do not include the `alliance` field in the score breakdown keys.

### Event Match Stats

TODO, but add year to `tasks_io.handlers.math.event_matchstats_calc`

### Tiebreakers

TODO

### Playoff Advancement

TODO

### Insights

TODO

### Ranking Sort Orders

TODO

### Predictions

TODO

### Event Rankings

TODO, but `EventDetails.renderable_rankings` needs updating and explain how/why
