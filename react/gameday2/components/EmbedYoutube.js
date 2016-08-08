import React, { PropTypes } from 'react'

export default React.createClass({
  propTypes: {
    webcast: PropTypes.object.isRequired,
  },
  render() {
    let src = '//www.youtube.com/embed/' + this.props.webcast.channel
    return (
      <iframe
        width="100%"
        height="100%"
        src={src}
        frameBorder="0"
        allowFullScreen
      ></iframe>
    )
  },
})
