import React, { PropTypes } from 'react';
import VideoCellOverlay from './VideoCellOverlay';
import WebcastSelectionPanel from './WebcastSelectionPanel'
import EmbedUstream from './EmbedUstream';
import EmbedYoutube from './EmbedYoutube';
import EmbedTwitch from './EmbedTwitch';

var VideoCell = React.createClass({
  propTypes: {
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    location: PropTypes.number.isRequired,
    removeWebcast: PropTypes.func.isRequired,
    addWebcastAtLocation: PropTypes.func.isRequired
  },
  getInitialState: function() {
    return {
      showOverlay: false,
      showWebcastSelectionPanel: false
    };
  },
  onMouseOver: function() {
    this.setState({"showOverlay": true})
  },
  onMouseOut: function() {
    this.setState({"showOverlay": false})
  },
  showWebcastSelectionPanel: function() {
    this.setState({"showWebcastSelectionPanel": true})
  },
  hideWebcastSelectionPanel: function() {
    this.setState({"showWebcastSelectionPanel": false})
  },
  webcastSelected: function(webcastId) {
    this.props.addWebcastAtLocation(webcastId, this.props.location)
    hideWebcastSelectionPanel()
  },
  render: function() {
    var classes = 'video-cell video-' + this.props.location;

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
          onMouseOut={this.onMouseOut} >
          {cellEmbed}
          <VideoCellOverlay
            webcast={this.props.webcast}
            enabled={this.state.showOverlay}
            removeWebcast={this.props.removeWebcast}
            showWebcastSelectionPanel={this.showWebcastSelectionPanel} />
          <WebcastSelectionPanel
            webcasts={this.props.webcasts}
            webcastsById={this.props.webcastsById}
            enabled={this.state.showWebcastSelectionPanel}
            webcastSelected={this.webcastSelected}
            closeWebcastSelectionPanel={this.hideWebcastSelectionPanel} />
        </div>
      )
    } else {
      return <div className={classes} >
        <div className="jumbotron">
          <p>Webcast selection will go here eventually.</p>
        </div>
      </div>
    }
  }
});

export default VideoCell;
