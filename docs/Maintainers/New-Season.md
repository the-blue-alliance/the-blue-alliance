## Kickoff

The [landing page config](https://www.thebluealliance.com/admin/main_landing) and the [GameDay config](https://www.thebluealliance.com/admin/gameday) can be used for most of the Kickoff-related tasks.

Before kickoff, set the landing page type to be `Kickoff`. A `kickoff_facebook_fbid` and `game_teaser_youtube_id` can be configured in the landing page config to show a game teaser video, as well as link to a Facebook event for Kickoff. The page will update with a link to the GameDay `/watch/kickoff` link automatically once Kickoff is within the next 24 hours. Ensure there is a `kickoff` URL alias in the GameDay config URL aliases that auto-plays the `firstinspires` stream.

Once the game is announced, the landing page type should be changed to `Build Season`. Update the `game_animation_youtube_id`, `game_name`, `manual_password`, and `build_handler_show_password` properties accordingly. To show a button to link to Robot in 3 Days streams in GameDay, set the `build_handler_show_ri3d` to be `True`. Ensure there is a `ri3d` URL alias in the GameDay config URL aliases that auto-plays the Ri3D streams.
