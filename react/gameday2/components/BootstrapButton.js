import React, { PropTypes } from 'react';
var classNames = require('classnames');

var BootstrapButton = React.createClass({
  propTypes: {
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
      // If the button has a callback to handle the click, prevent the default
      event.preventDefault()
      this.props.handleClick();
    }
  },
  render: function() {
    var classes = classNames({
      'btn': true,
      'btn-default': true,
      'navbar-btn': true,
      'active': this.props.active,
    });
    return (
      <button type="button" className={classes} href={this.props.a} onClick={this.handleClick}>{this.props.children}</button>
    );
  }
});

export default BootstrapButton;
