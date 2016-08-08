import React, { PropTypes } from 'react'

export default React.createClass({
  propTypes: {
    data_toggle: PropTypes.string,
    data_target: PropTypes.string,
    a: PropTypes.string,
    handleClick: PropTypes.func,
  },
  getDefaultProps() {
    return {
      a: '#',
    }
  },
  handleClick(event) {
    if (this.props.handleClick) {
      // If a callback to handle the click is given, prevent the default behavior
      event.preventDefault()
      this.props.handleClick()
      return false
    }
  },
  render() {
    return (
      <li data-toggle={this.props.data_toggle} data-target={this.props.data_target}><a href={this.props.a} onClick={this.handleClick}>{this.props.children}</a></li>
    )
  },
})
