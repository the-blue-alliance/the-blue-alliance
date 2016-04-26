import React, { PropTypes } from 'react';
import WebcastListItem from './WebcastListItem';
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem';

var WebcastDropdown = React.createClass({
  propTypes: {
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    onWebcastAdd: PropTypes.func.isRequired,
    onWebcastReset: PropTypes.func.isRequired
  },
  render: function() {
    var webcastListItems = [];
    if (this.props.webcasts) {
      for (var i = 0; i < this.props.webcasts.length; i++) {
        var webcast = this.props.webcastsById[this.props.webcasts[i]];
        webcastListItems.push(
          <WebcastListItem
            key={webcast.id}
            webcast={webcast}
            onWebcastAdd={this.props.onWebcastAdd} />
        );
      }
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

export default WebcastDropdown;
