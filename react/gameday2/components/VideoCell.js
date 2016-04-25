import React from 'react';
import VideoCellOverlay from './VideoCellOverlay';
import EmbedUstream from './EmbedUstream';
import EmbedYoutube from './EmbedYoutube';
import EmbedTwitch from './EmbedTwitch';

var VideoCell = React.createClass({
  getInitialState: function() {
    return {
      showOverlay: false,
    };
  },
  onMouseOver: function(event) {
    this.setState({"showOverlay": true})
  },
  onMouseOut: function(event) {
    this.setState({"showOverlay": false})
  },
  render: function() {
    var classes = 'video-cell video-' + this.props.num;

    if (this.props.webcast) {
      var cellEmbed;
      switch (this.props.webcast.type) {
        case 'ustream':
        cellEmbed = <EmbedUstream
          webcast={this.props.webcast}
          vidHeight={this.props.vidHeight}
          vidWidth={this.props.vidWidth} />;
        break;
        case 'youtube':
        cellEmbed = <EmbedYoutube
          webcast={this.props.webcast}
          vidHeight={this.props.vidHeight}
          vidWidth={this.props.vidWidth} />;
        break;
        case 'twitch':
        cellEmbed = <EmbedTwitch
          webcast={this.props.webcast}
          vidHeight={this.props.vidHeight}
          vidWidth={this.props.vidWidth} />;
        break;
        default:
        cellEmbed = "";
        break;
      }

      return (
        <div className={classes}
          idName={this.props.webcast.id}
          onMouseOver={this.onMouseOver}
          onMouseOut={this.onMouseOut}>
          {cellEmbed}
          <VideoCellOverlay
            webcast={this.props.webcast}
            enabled={this.state.showOverlay}
            onWebcastRemove={this.props.onWebcastRemove} />
        </div>
      )
    } else {
      return <div className={classes} />
    }
  }
});

export default VideoCell;
