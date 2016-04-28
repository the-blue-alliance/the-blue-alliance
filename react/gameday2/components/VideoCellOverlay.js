import React, { PropTypes } from 'react';
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
      return (
        <div className={classes}>
          <div className="panel-heading">
            <h3 className="panel-title">{this.props.webcast.name}</h3>
            <div className="overlay-button-container">
              <a className="overlay-button" href="#" onClick={this.props.showWebcastSelectionPanel}>Change Webcast</a>
              <span className="overlay-button button-close glyphicon glyphicon-remove" onClick={this.onCloseClicked}></span>
            </div>
          </div>
        </div>
      )
    }
  }
});

export default VideoCellOverlay;
