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
      <button type="button" className="list-group-item" onClick={this.handleClick}>{this.props.webcast.name}</button>
    )
  }
})

export default WebcastSelectionPanelItem
