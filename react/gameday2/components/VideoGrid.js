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
 *
 * Due to a quirk in how browsers treat iframes, once we create an iframe, we
 * can't change its position in the DOM, or else it will reload. That slightly
 * complicates how we have to render things, especially given how React abstracts
 * away control of the DOM. We have to be careful to render each VideoCell in the
 * same order each time.
 *
 * We will use the following algorithm to ensure that webcasts are always rendered
 * in the same order in the DOM:
 *
 * 1. Iterate through each key in displayedWebcasts.
 * 2. If the key is present in webcastRenderOrder, don't add it to webcastRenderOrder
 * 3. If the key is not present in webcastRenderOrder, put it in the next
 * empty index of webcastRenderOrder
 * 4. After steps 1-3, webcastRenderOrder will contain all of the keys from
 * displayedWebcasts
 * 5. Iterate through each key in webcastRenderOrder
 * 6. For each key, generate a VideoCell component with the appropriate key and
 * props. The location should be determined by looking up the index of the webcast
 * ID in displayedWebcasts.
 * 7. After steps 5-6, we will have a VideoCell for each of the dispalyed webcasts.
 * 8. While the number of VideoCells is less than
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
  getInitialState: function() {
    return {
      webcastRenderOrder: []
    }
  },
  componentWillMount: function() {
    this.updateWebcastRenderOrder(this.props)
  },
  componentWillReceiveProps: function(nextProps) {
    this.updateWebcastRenderOrder(nextProps)
  },
  updateWebcastRenderOrder: function(props) {
    let webcastRenderOrder = this.state.webcastRenderOrder.slice(0)

    // First, remove any webcasts that are no londer in displayedWebcasts
    for (let i = 0; i < webcastRenderOrder.length; i++) {
      if (props.displayedWebcasts.indexOf(webcastRenderOrder[i]) == -1) {
        webcastRenderOrder[i] = null
      }
    }

    // Now, add any new webcasts in the first available space
    for (let i = 0; i < props.displayedWebcasts.length; i++) {
      if (webcastRenderOrder.indexOf(props.displayedWebcasts[i]) == -1) {
        // Find the first empty space in webcastRenderOrder
        let foundSpace = false
        for (let j = 0; j < webcastRenderOrder.length; j++) {
          if (!webcastRenderOrder[j]) {
            foundSpace = true
            webcastRenderOrder[j] = props.displayedWebcasts[i]
            break
          }
        }
        if (!foundSpace) {
          webcastRenderOrder.push(props.displayedWebcasts[i])
        }
      }
    }

    this.setState({
      webcastRenderOrder
    })
  },
  renderEmptyLayout: function(classes) {
    return (
      <LayoutSelectionPanel setLayout={this.props.setLayout}/>
    )
  },
  renderLayout: function(webcastCount, layoutNumber, classes) {
    classes += (' layout-' + layoutNumber)

    let webcastRenderOrder = this.state.webcastRenderOrder

    // Now, compute which locations will be empty
    let emptyCellLocations = []
    for (let i = 0; i < webcastCount; i++) {
      if (!this.props.displayedWebcasts[i]) {
        emptyCellLocations.push(i)
      }
    }

    // Now, render everything!

    let videoCells = []
    for (let i = 0; i < webcastCount; i++) {
      let webcast = null;
      let id = 'video-' + i;
      let location = null;
      if (webcastRenderOrder[i]) {
        webcast = this.props.webcastsById[webcastRenderOrder[i]]
        id = webcast.id
        location = this.props.displayedWebcasts.indexOf(id)
      } else {
        location = emptyCellLocations.shift()
      }

      videoCells.push(
        <VideoCell
          location={location}
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
    )

    /*var videoCells = [];
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
    );*/
  },
  render: function() {
    var classes = classNames({
      'video-grid': true,
      'leave-left-margin': this.props.hashtagSidebarVisible,
      'leave-right-margin': this.props.chatSidebarVisible,
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
