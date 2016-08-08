import React, { PropTypes } from 'react'

var LayoutDropdownItem = React.createClass({
  propTypes: {
    layoutId: PropTypes.number.isRequired,
    handleClick: PropTypes.func.isRequired
  },
  handleClick: function(event) {
    if (this.props.handleClick) {
      event.preventDefault()
      this.props.handleClick(this.props.layoutId)
    }
  },
  render: function() {
    return (
      <li onClick={this.handleClick}><a href='#'>{this.props.children}</a></li>
    )
  },
})

export default LayoutDropdownItem
