import React, { PropTypes } from 'react';

var BootstrapNavDropdownListItem = React.createClass({
  propTypes: {
    data_toggle: PropTypes.string,
    data_target: PropTypes.string,
    a: PropTypes.string,
    handleClick: PropTypes.func
  },
  getDefaultProps: function() {
    return {
      a: '#'
    };
  },
  handleClick: function(event) {
    if (this.props.handleClick) {
      // If a callback to handle the click is given, prevent the default behavior
      event.preventDefault()
      this.props.handleClick();
      return false;
    }
  },
  render: function() {
    return (
      <li data-toggle={this.props.data_toggle} data-target={this.props.data_target}><a href={this.props.a} onClick={this.handleClick}>{this.props.children}</a></li>
    )
  },
});

export default BootstrapNavDropdownListItem;
