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
      return (
        <div className={classes}>
          <div className="panel-heading">
            <h3 className="panel-title">{this.props.webcast.name}</h3>
            <div className="overlay-button-container">
              <OverlayTrigger placement="bottom" overlay={changeWebcastTooltip}>
                <span className="overlay-button" onClick={this.props.showWebcastSelectionPanel}>Change Webcast</span>
              </OverlayTrigger>
              <OverlayTrigger placement="bottom" overlay={closeTooltip}>
                <span className="overlay-button button-close glyphicon glyphicon-remove" onClick={this.onCloseClicked}></span>
              </OverlayTrigger>
            </div>
          </div>
        </div>
      )
    }
  }
});

export default VideoCellOverlay;
