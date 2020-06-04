## For Event Webcasts

List of dicts where each dict is as follows:

**Livestream:** `{"type": "livestream", "channel": "<channel id #>", "file": "<event id #>"}`
* Example: `{"type": "livestream", "channel": "3136927", "file": "1964881"}`

**Twitch TV:** `{"type": "twitch", "channel": "<channel name>"}`
* Example: `{"type": "twitch", "channel": "tbacast"}`

**Ustream:** `{"type": "ustream", "channel": "<channel id #>"}`
* Example: `{"type": "ustream", "channel": "6540154"}`

**RTMP:** `{"type": "rtmp", "channel": "<stream URL>", "file": "<file name>"}`
* Example: `{"type": "rtmp", "channel": "s3b78u0kbtx79q.cloudfront.net/cfx/st/", "file": "mp4:bauhaus"}`
* **Important**: Don't include the `rtmp://` protocol prefix on the stream URL

**HTML5 (HLS):** `{"type": "html5", "channel": "<stream URL>"}`
* Example: `{"type": "html5", "channel": "http://solutions.brightcove.com/jwhisenant/hls/apple/bipbop/bipbopall.m3u8"}`

## For Special Webcasts
The `gameday.special_webcasts` sitevar contains information about extra webcasts as well as other metadata for GameDay.
**Example:** 
```json
{
  "webcasts": [
    {
      "key_name": "firstupdatesnow",
      "type": "twitch",
      "name": "FIRST Updates Now",
      "channel": "firstupdatesnow"
    },
    {
      "key_name": "gamesense",
      "type": "twitch",
      "name": "GameSense",
      "channel": "frcgamesense"
    }
  ],
  "aliases": {
    "fun": "#layout=0&view_0=firstupdatesnow-1",
    "gamesense": "#layout=0&view_0=frcgamesense-1"
  }
}
```