import React, { PropTypes } from 'react';
import VideoCell from './VideoCell';
import { getNumViewsForLayout } from '../utils/layoutUtils'
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
  propTypes: {
    displayedWebcasts: PropTypes.array.isRequired,
    layoutId: PropTypes.number.isRequired,
    layoutSet: PropTypes.bool.isRequired
  },
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
      // Some entries in the dispalyed webcasts array may be null, for instance
      // if the user doesn't select webcasts for some views in a layout
      if (i < this.props.displayedWebcasts.length && this.props.displayedWebcasts[i]) {
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

    // If the user didn't set a layout yet, show the empty "welcome" view
    if (!this.props.layoutSet) {
      return this.renderEmptyLayout(classes)
    }

    let selectedLayoutId = this.props.layoutId
    let numViews = getNumViewsForLayout(selectedLayoutId)
    return this.renderLayout(numViews, selectedLayoutId, classes)
  }
});

export default VideoGrid;
