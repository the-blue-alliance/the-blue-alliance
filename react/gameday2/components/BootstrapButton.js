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
  handleClick: function() {
    if (this.props.handleClick) {
      this.props.handleClick();
      return false;
    }
  },
  render: function() {
    var classes = classNames({
      'btn': true,
      'btn-default': true,
      'active': this.props.active,
    });
    return (
      <a className={classes} href={this.props.a} onClick={this.handleClick}>{this.props.children}</a>
    );
  }
});

export default BootstrapButton;
