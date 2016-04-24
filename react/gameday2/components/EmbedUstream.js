import React, { PropTypes } from 'react';

var EmbedUstream = React.createClass({
  propTypes: {
    webcast: PropTypes.object.isRequired
  },
  render: function() {
    var channel = this.props.webcast.channel;
    var src = `http://www.ustream.tv/embed/${channel}?html5ui=1`;
    return (
      <iframe
        width={this.props.vidWidth}
        height={this.props.vidHeight}
        src={src}
        scrolling="no"
        allowfullscreen
        webkitallowfullscreen
        frameborder="0"
        style={{border: "0 none transparent"}}></iframe>
    );
  }
});

export default EmbedUstream;
