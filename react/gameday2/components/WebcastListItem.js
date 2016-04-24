import React, { PropTypes } from 'react';
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem';

var WebcastListItem = React.createClass({
  propTypes: {
    onWebcastAdd: PropTypes.func.isRequired
  },
  handleClick: function() {
    this.props.onWebcastAdd(this.props.webcast);
  },
  render: function() {
    return <BootstrapNavDropdownListItem handleClick={this.handleClick}>{this.props.webcast.name}</BootstrapNavDropdownListItem>
  },
});

export default WebcastListItem;
