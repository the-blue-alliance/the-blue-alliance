import React from 'react';
var classNames = require('classnames');

var VideoCellOverlay = React.createClass({
  onCloseClicked: function() {
    this.props.onWebcastRemove(this.props.webcast);
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
            <span className="button-close glyphicon glyphicon-remove" onClick={this.onCloseClicked}></span>
          </div>
        </div>
      )
    }
  }
});

export default VideoCellOverlay;
