import React, { PropTypes } from 'react'

export default React.createClass({
  propTypes: {
    children: PropTypes.node,
    layoutId: PropTypes.number.isRequired,
    handleClick: PropTypes.func.isRequired,
  },
  handleClick(event) {
    if (this.props.handleClick) {
      event.preventDefault()
      this.props.handleClick(this.props.layoutId)
    }
  },
  render() {
    return (
      <li onClick={this.handleClick}><a href="#">{this.props.children}</a></li>
    )
  },
})
