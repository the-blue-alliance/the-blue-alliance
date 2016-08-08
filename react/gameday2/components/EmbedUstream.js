import React, { PropTypes } from 'react'

export default React.createClass({
  propTypes: {
    webcast: PropTypes.object.isRequired,
  },
  render() {
    const channel = this.props.webcast.channel
    let src = `http://www.ustream.tv/embed/${channel}?html5ui=1`
    return (
      <iframe
        width="100%"
        height="100%"
        src={src}
        scrolling="no"
        allowFullScreen
        frameBorder="0"
        style={{ border: '0 none transparent' }}
      ></iframe>
    )
  },
})
