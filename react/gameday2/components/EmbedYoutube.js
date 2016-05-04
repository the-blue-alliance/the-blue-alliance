import React, { PropTypes } from 'react';

var EmbedYoutube = React.createClass({
  propTypes: {
    webcast: PropTypes.object.isRequired
  },
  render: function() {
    var src = "//www.youtube.com/embed/" + this.props.webcast.channel;
    return (
      <iframe
        width={this.props.vidWidth}
        height={this.props.vidHeight}
        src={src}
        frameBorder="0"
        allowFullScreen>
      </iframe>
    );
  }
});

export default EmbedYoutube;
