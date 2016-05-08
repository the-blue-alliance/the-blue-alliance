import React, { PropTypes } from 'react';
import { Tooltip, OverlayTrigger } from 'react-bootstrap'
var classNames = require('classnames');

var VideoCellOverlay = React.createClass({
  propTypes: {
    enabled: PropTypes.bool.isRequired,
    webcast: PropTypes.object.isRequired,
    showWebcastSelectionPanel: PropTypes.func.isRequired
  },
  onCloseClicked: function() {
    this.props.removeWebcast(this.props.webcast.id);
  },
  render: function() {
    var classes = classNames({
      'hidden': !this.props.enabled,
      'panel': true,
      'panel-default': true,
      'video-cell-overlay': true,
    });
    if (this.props.webcast) {
      const closeTooltip = (
        <Tooltip>Close webcast</Tooltip>
      )
      const changeWebcastTooltip = (
        <Tooltip>Change webcast</Tooltip>
      )
      const swapWebcastTooltip = (
        <Tooltip>Swap webcast position</Tooltip>
      )
      return (
        <div className={classes}>
          <div className="panel-heading">
            <h3 className="panel-title">{this.props.webcast.name}</h3>
            <div className="overlay-button-container">
              <OverlayTrigger placement="bottom" overlay={swapWebcastTooltip}>
                <i className="material-icons overlay-button">compare_arrows</i>
              </OverlayTrigger>
              <OverlayTrigger placement="bottom" overlay={changeWebcastTooltip}>
                <i className="material-icons overlay-button" onClick={this.props.showWebcastSelectionPanel}>videocam</i>
              </OverlayTrigger>
              <OverlayTrigger placement="bottom" overlay={closeTooltip}>
                <i className="material-icons overlay-button button-close" onClick={this.onCloseClicked}>close</i>
              </OverlayTrigger>
            </div>
          </div>
        </div>
      )
    }
  }
});

export default VideoCellOverlay;
