import React, { PropTypes } from 'react'

const WebcastSelectionPanelItem = React.createClass({
  propTypes: {
    webcast: PropTypes.object.isRequired,
    webcastSelected: PropTypes.func.isRequired,
  },
  handleClick() {
    this.props.webcastSelected(this.props.webcast.id)
  },
  render() {
    return (
      <button type="button" className="list-group-item" onClick={this.handleClick}>{this.props.webcast.name}</button>
    )
  },
})

export default WebcastSelectionPanelItem
