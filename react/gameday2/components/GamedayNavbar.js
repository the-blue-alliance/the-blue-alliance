import React, { PropTypes } from 'react';
import BootstrapButton from './BootstrapButton';
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem';
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

var SettingsDropdown = React.createClass({
  render: function() {
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle" data-toggle="dropdown"><span className="glyphicon glyphicon-cog"></span></a>
        <ul className="dropdown-menu">
          <BootstrapNavDropdownListItem
            data_toggle="modal"
            data_target="#followingTeamsModal">Follow Teams</BootstrapNavDropdownListItem>
          <li className="divider"></li>
          <BootstrapNavDropdownListItem>Debug Menu</BootstrapNavDropdownListItem>
          <BootstrapNavDropdownListItem>TODO Show Beeper</BootstrapNavDropdownListItem>
        </ul>
      </li>
    );
  }
});

var WebcastListItem = React.createClass({
  handleClick: function() {
    this.props.onWebcastAdd(this.props.webcast);
  },
  render: function() {
    return <BootstrapNavDropdownListItem handleClick={this.handleClick}>{this.props.webcast.name}</BootstrapNavDropdownListItem>
  },
});

export default GamedayNavbar
