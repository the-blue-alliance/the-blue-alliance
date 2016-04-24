import React, { PropTypes } from 'react';
import BootstrapButton from './BootstrapButton';
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem';
import WebcastListItem from './WebcastListItem';
import SettingsDropdown from './SettingsDropdown';
var classNames = require('classnames');

var GamedayNavbar = React.createClass({
  propTypes: {
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    hashtagEnabled: PropTypes.bool.isRequired,
    chatEnabled: PropTypes.bool.isRequired,
    onWebcastAdd: PropTypes.func.isRequired,
    onWebcastReset: PropTypes.func.isRequired,
    onHashtagToggle: PropTypes.func.isRequired,
    onChatToggle: PropTypes.func.isRequired
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
            <WebcastDropdown
              webcasts={this.props.webcasts}
              webcastsById={this.props.webcastsById}
              onWebcastAdd={this.props.onWebcastAdd}
              onWebcastReset={this.props.onWebcastReset} />
            <li>
              <BootstrapButton
                active={this.props.hashtagEnabled}
                handleClick={this.props.onHashtagToggle}>Hashtags</BootstrapButton>
            </li>
            <li>
              <BootstrapButton
                active={this.props.chatEnabled}
                handleClick={this.props.onChatToggle}>Chat</BootstrapButton>
            </li>
            <SettingsDropdown />
          </ul>
        </div>
      </nav>
    );
  }
});

var WebcastDropdown = React.createClass({
  render: function() {
    var webcastListItems = [];
    for (var i = 0; i < this.props.webcasts.length; i++) {
      var webcast = this.props.webcastsById[this.props.webcasts[i]];
      webcastListItems.push(
        <WebcastListItem
          key={webcast.id}
          webcast={webcast}
          onWebcastAdd={this.props.onWebcastAdd} />
      );
    }
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle" data-toggle="dropdown">Add Webcasts <b className="caret"></b></a>
        <ul className="dropdown-menu">
          {webcastListItems}
          <li className="divider"></li>
          <BootstrapNavDropdownListItem handleClick={this.props.onWebcastReset}>Reset Webcasts</BootstrapNavDropdownListItem>
        </ul>
      </li>
    );
  }
});

export default GamedayNavbar;
