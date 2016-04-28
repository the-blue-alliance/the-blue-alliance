import React, { PropTypes } from 'react'

var EmbedTwitch = React.createClass({
  propTypes: {
    webcast: PropTypes.object.isRequired
  },
  render: function() {
    var channel = this.props.webcast.channel
    let iframeSrc = `https://player.twitch.tv/?channel=${channel}&html5`
    return (
      <iframe src={iframeSrc} frameborder="0" scrolling="no" height="100%" width="100%"></iframe>
    )
  }
})

export default EmbedTwitch
