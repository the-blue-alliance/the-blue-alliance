import React, { PropTypes } from 'react';
import VideoCell from './VideoCell';
import LayoutSelectionPanel from './LayoutSelectionPanel'
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
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    layoutId: PropTypes.number.isRequired,
    layoutSet: PropTypes.bool.isRequired,
    addWebcastAtLocation: PropTypes.func.isRequired,
    setLayout: PropTypes.func.isRequired
  },
  renderEmptyLayout: function(classes) {
    return (
      <LayoutSelectionPanel setLayout={this.props.setLayout}/>
    )
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
          location={i}
          key={id}
          webcast={webcast}
          webcasts={this.props.webcasts}
          webcastsById={this.props.webcastsById}
          displayedWebcasts={this.props.displayedWebcasts}
          addWebcastAtLocation={this.props.addWebcastAtLocation}
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
