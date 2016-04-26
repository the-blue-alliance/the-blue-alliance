import React, { PropTypes } from 'react';
import WebcastListItem from './WebcastListItem';
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem';

var WebcastDropdown = React.createClass({
  propTypes: {
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    addWebcast: PropTypes.func.isRequired,
    resetWebcasts: PropTypes.func.isRequired
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
            addWebcast={this.props.addWebcast} />
        );
      }
    }
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle" data-toggle="dropdown">Add Webcasts <b className="caret"></b></a>
        <ul className="dropdown-menu">
          {webcastListItems}
          <li className="divider"></li>
          <BootstrapNavDropdownListItem handleClick={this.props.resetWebcasts}>Reset Webcasts</BootstrapNavDropdownListItem>
        </ul>
      </li>
    );
  }
});

export default WebcastDropdown;
