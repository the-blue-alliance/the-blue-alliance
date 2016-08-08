import React, { PropTypes } from 'react'
import classNames from 'classnames'

export default React.createClass({
  propTypes: {
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
      // If the button has a callback to handle the click, prevent the default
      event.preventDefault()
      this.props.handleClick()
    }
  },
  render() {
    const classes = classNames({
      'btn': true,
      'btn-default': true,
      'navbar-btn': true,
    })
    return (
      <button type="button" className={classes} href={this.props.a} onClick={this.handleClick}>{this.props.children}</button>
    )
  },
})
