import React, { PropTypes } from 'react';
import BootstrapButton from './BootstrapButton';
import SettingsDropdown from './SettingsDropdown';
import WebcastDropdown from './WebcastDropdown';
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
        <div className="navbar-header">
          <button type="button" className="navbar-toggle" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
            <span className="sr-only">Toggle navigation</span>
            <span className="icon-bar"></span>
            <span className="icon-bar"></span>
            <span className="icon-bar"></span>
          </button>
          <a className="navbar-brand" href="#">Gameday</a>
        </div>

        <div className="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
          <ul className="nav navbar-nav navbar-right">
            <LayoutDropdown setLayout={this.props.setLayout} />
            <WebcastDropdown
              webcasts={this.props.webcasts}
              webcastsById={this.props.webcastsById}
              addWebcast={this.props.addWebcast}
              resetWebcasts={this.props.resetWebcasts} />
            <li>
              <BootstrapButton
                active={this.props.hashtagPanelVisible}
                handleClick={this.props.toggleHashtagPanelVisibility}>Hashtags</BootstrapButton>
            </li>
            <li>
              <BootstrapButton
                active={this.props.chatPanelVisible}
                handleClick={this.props.toggleChatPanelVisibility}>Chat</BootstrapButton>
            </li>
            <SettingsDropdown />
          </ul>
        </div>
      </nav>
    );
  }
});

export default GamedayNavbar;
