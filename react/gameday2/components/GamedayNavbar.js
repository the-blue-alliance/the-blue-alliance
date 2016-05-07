import React, { PropTypes } from 'react';
import BootstrapButton from './BootstrapButton';
import SettingsDropdown from './SettingsDropdown';
import SidePanelToggleDropdown from './SidePanelToggleDropdown'
import LayoutDropdown from './LayoutDropdown';
var classNames = require('classnames');

var GamedayNavbar = React.createClass({
  propTypes: {
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    hashtagPanelVisible: PropTypes.bool.isRequired,
    chatPanelVisible: PropTypes.bool.isRequired,
    addWebcast: PropTypes.func.isRequired,
    resetWebcasts: PropTypes.func.isRequired,
    toggleHashtagPanelVisibility: PropTypes.func.isRequired,
    toggleChatPanelVisibility: PropTypes.func.isRequired,
    setLayout: PropTypes.func.isRequired
  },
  render: function() {
    return (
      <nav className="navbar navbar-default navbar-fixed-top" role="navigation">
        <div className="container-fluid">
          <div className="navbar-header">
            <button type="button" className="navbar-toggle" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
              <span className="sr-only">Toggle navigation</span>
              <span className="icon-bar"></span>
              <span className="icon-bar"></span>
              <span className="icon-bar"></span>
            </button>
            <span className="navbar-brand">Gameday</span>
          </div>

          <div className="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
            <ul className="nav navbar-nav navbar-right">
              <LayoutDropdown setLayout={this.props.setLayout} />
              <SidePanelToggleDropdown
                toggleChatPanelVisibility={this.props.toggleChatPanelVisibility}
                toggleHashtagPanelVisibility={this.props.toggleHashtagPanelVisibility}
                chatPanelVisible={this.props.chatPanelVisible}
                hashtagPanelVisible={this.props.hashtagPanelVisible} />
              <SettingsDropdown resetWebcasts={this.props.resetWebcasts} />
            </ul>
          </div>
        </div>
      </nav>
    );
  }
});

export default GamedayNavbar;
