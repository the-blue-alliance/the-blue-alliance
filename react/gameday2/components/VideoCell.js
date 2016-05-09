import React, { PropTypes } from 'react';
import VideoOverlayContainer from '../containers/VideoOverlayContainer';
import WebcastSelectionPanel from './WebcastSelectionPanel'
import EmbedUstream from './EmbedUstream';
import EmbedYoutube from './EmbedYoutube';
import EmbedTwitch from './EmbedTwitch';

var VideoCell = React.createClass({
  propTypes: {
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    displayedWebcasts: PropTypes.array.isRequired,
    location: PropTypes.number.isRequired,
    addWebcastAtLocation: PropTypes.func.isRequired
  },
  getInitialState: function() {
    return {
      mouseOver: false,
      showWebcastSelectionPanel: false
    };
  },
  onMouseOver: function() {
    this.setState({"mouseOver": true})
  },
  onMouseOut: function() {
    this.setState({"mouseOver": false})
  },
  showWebcastSelectionPanel: function() {
    this.setState({"showWebcastSelectionPanel": true})
  },
  hideWebcastSelectionPanel: function() {
    this.setState({"showWebcastSelectionPanel": false})
  },
  webcastSelected: function(webcastId) {
    this.props.addWebcastAtLocation(webcastId, this.props.location)
    this.hideWebcastSelectionPanel()
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
          <VideoOverlayContainer
            webcast={this.props.webcast}
            mouseOverContainer={this.state.mouseOver}
            location={this.props.location} />
        </div>
      )
    } else {
      return <div className={classes} >
        <div className="empty-view">
          <button type="button" className="btn btn-secondary" onClick={this.showWebcastSelectionPanel}>Select a webcast</button>
        </div>
        <WebcastSelectionPanel
          webcasts={this.props.webcasts}
          webcastsById={this.props.webcastsById}
          displayedWebcasts={this.props.displayedWebcasts}
          enabled={this.state.showWebcastSelectionPanel}
          webcastSelected={this.webcastSelected}
          closeWebcastSelectionPanel={this.hideWebcastSelectionPanel} />
      </div>
    }
  }
});

export default VideoCell;
