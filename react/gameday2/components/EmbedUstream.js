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
        width={this.props.vidWidth}
        height={this.props.vidHeight}
        src={src}
        scrolling="no"
        allowFullScreen
        webkitallowfullscreen
        frameBorder="0"
        style={{ border: '0 none transparent' }}
      ></iframe>
    )
  },
})
