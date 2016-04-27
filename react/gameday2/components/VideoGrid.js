import React from 'react';
import VideoCell from './VideoCell';
var classNames = require('classnames');

/**
 * Responsible for rendering a number of webcasts in a grid-like
 * presentation.
 *
 * Should pr provided with both {webcasts} and {displayedWebcasts} as properties.
 * {webcasts} should be an array of webcast objects, and {displayedWebcasts}
 * should be an array of webcast ids.
 */
var VideoGrid = React.createClass({
  renderEmptyLayout: function(classes) {
    return (
      <div className={classes}>
        <div className="jumbotron">
          <h2>GameDay &mdash; Watch FIRST Webcasts</h2>
          <p>To get started, pick some webcasts from the top menu.</p>
        </div>
      </div>
    );
  },
  renderLayout: function(webcastCount, layoutNumber, classes) {
    classes += (' layout-' + layoutNumber);

    var videoCells = [];
    for (var i = 0; i < webcastCount; i++) {
      var webcast = null, id = 'video-' + i;
      if (i < this.props.displayedWebcasts.length) {
        webcast = this.props.webcastsById[this.props.displayedWebcasts[i]];
        id = webcast.id;
      }
      videoCells.push(
        <VideoCell
          num={i}
          key={id}
          webcast={webcast}
          removeWebcast={this.props.removeWebcast}
          vidHeight="100%"
          vidWidth="100%" />
      );
    }

    return (
      <div className={classes}>
        {videoCells}
      </div>
    );
  },
  render: function() {
    var classes = classNames({
      'video-grid': true,
      'leave-left-margin': this.props.hashtagPanelVisible,
      'leave-right-margin': this.props.chatPanelVisible,
    });
    var layout;
    switch (this.props.displayedWebcasts.length) {
      case 0:
      layout = this.renderEmptyLayout(classes);
      break;
      case 1:
      layout = this.renderLayout(1, 1, classes);
      break;
      case 2:
      layout = this.renderLayout(2, 2, classes);
      break;
      case 3:
      layout = this.renderLayout(3, 3, classes);
      break;
      case 4:
      layout = this.renderLayout(4, 4, classes);
      break;
    }
    return layout;
  },
});

export default VideoGrid;
