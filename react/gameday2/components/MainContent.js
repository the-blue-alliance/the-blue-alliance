import React, { PropTypes } from 'react'
import VideoGridContainer from '../containers/VideoGridContainer';
import LayoutSelectionPanel from './LayoutSelectionPanel'
import NoWebcasts from './NoWebcasts'

var classNames = require('classnames')

/**
 * Acts as a high-level "controller" for the main content area. This component
 * will render the appropriate child based on the state of the app. This will
 * also apply the appropriate margins to the main content area to position it
 * correctly when the sidebars are shown or hidden.
 *
 * If no webcasts are present, this displays a message for that.
 *
 * If webcasts are present but no layout is set, this displays a layout selector.
 *
 * If webcasts are present and a layout is set, this displays the video grid.
 */
var MainContent = React.createClass({
  propTypes: {
    webcasts: PropTypes.array.isRequired,
    hashtagSidebarVisible: PropTypes.bool.isRequired,
    chatSidebarVisible: PropTypes.bool.isRequired,
    layoutSet: PropTypes.bool.isRequired
  },
  render: function() {
    let child = null

    if (this.props.webcasts.length == 0) {
      // No webcasts. Do the thing!
      child = (
        <NoWebcasts />
      )
    } else if (!this.props.layoutSet) {
      // No layout set. Display the layout selector.
      child = (
        <LayoutSelectionPanel setLayout={this.props.setLayout}/>
      )
    } else {
      // Display the video grid
      child = (
        <VideoGridContainer />
      )
    }

    var classes = classNames({
      'content': true,
      'leave-left-margin': this.props.hashtagSidebarVisible,
      'leave-right-margin': this.props.chatSidebarVisible,
    });

    return (
      <div className={classes}>
        {child}
      </div>
    )
  }
})

export default MainContent
