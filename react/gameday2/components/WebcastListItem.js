import React, { PropTypes } from 'react';
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem';

var WebcastListItem = React.createClass({
  propTypes: {
    addWebcast: PropTypes.func.isRequired
  },
  handleClick: function() {
    this.props.addWebcast(this.props.webcast.id);
  },
  render: function() {
    return <BootstrapNavDropdownListItem handleClick={this.handleClick}>{this.props.webcast.name}</BootstrapNavDropdownListItem>
  },
});

export default WebcastListItem;
