import React from 'react';
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem';

var WebcastListItem = React.createClass({
  handleClick: function() {
    this.props.onWebcastAdd(this.props.webcast);
  },
  render: function() {
    return <BootstrapNavDropdownListItem handleClick={this.handleClick}>{this.props.webcast.name}</BootstrapNavDropdownListItem>
  },
});

export default WebcastListItem;
