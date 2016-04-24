import React, { PropTypes } from 'react';

var EmbedTwitch = React.createClass({
  propTypes: {
    webcast: PropTypes.object.isRequired
  },
  render: function() {
    var channel = this.props.webcast.channel;
    var src = `http://www.twitch.tv/widgets/live_embed_player.swf?channel=${channel}`;
    var flashvars = `hostname=www.twitch.tv&channel=${channel}&auto_play=true&start_volume=25&enable_javascript=true`;
    return (
      <object
        type='application/x-shockwave-flash'
        height='100%'
        width='100%'
        id='live_embed_player_flash'
        data={src}
        bgcolor='#000000'>
        <param name='allowFullScreen' value='true' />
        <param name='allowScriptAccess' value='always' />
        <param name='allowNetworking' value='all' />
        <param
          name='movie'
          value='http://www.twitch.tv/widgets/live_embed_player.swf' />
        <param
          name='flashvars'
          value={flashvars} />
        <param name='wmode' value='transparent' />
      </object>
    );
  }
});

export default EmbedTwitch;
