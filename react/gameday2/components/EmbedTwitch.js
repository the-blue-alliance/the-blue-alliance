import React, { PropTypes } from 'react'

export default React.createClass({
  propTypes: {
    webcast: PropTypes.object.isRequired,
  },
  render() {
    const channel = this.props.webcast.channel
    let iframeSrc = `https://player.twitch.tv/?channel=${channel}`
    return (
      <iframe
        src={iframeSrc}
        frameBorder="0"
        scrolling="no"
        height="100%"
        width="100%"
      ></iframe>
    )
  },
})
