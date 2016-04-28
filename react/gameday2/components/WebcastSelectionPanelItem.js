import React, { PropTypes } from 'react'

let WebcastSelectionPanelItem = React.createClass({
  propTypes: {
    webcast: PropTypes.object.isRequired,
    webcastSelected: PropTypes.func.isRequired
  },
  handleClick: function() {
    this.props.webcastSelected(this.props.webcast.id)
  },
  render: function() {
    return (
      <a href="#" className="list-group-item" onClick={this.handleClick}>{this.props.webcast.name}</a>
    )
  }
})

export default WebcastSelectionPanelItem
