import React, { PropTypes } from 'react'
import BootstrapDropdownToggleItem from './BootstrapDropdownToggleItem'

var SettingsDropdown = React.createClass({
  propTypes: {
    toggleChatPanelVisibility: PropTypes.func.isRequired,
    toggleHashtagPanelVisibility: PropTypes.func.isRequired,
    chatPanelVisible: PropTypes.bool.isRequired,
    hashtagPanelVisible: PropTypes.bool.isRequired
  },
  toggleHashtagPanelVisibility: function(e) {
    if (this.props.toggleHashtagPanelVisibility) {
      e.preventDefault()
      e.stopPropagation()
      this.props.toggleHashtagPanelVisibility()
    }
  },
  toggleChatPanelVisibility: function(e) {
    if (this.props.toggleChatPanelVisibility) {
      e.preventDefault()
      e.stopPropagation()
      this.props.toggleChatPanelVisibility()
    }
  },
  render: function() {
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle" data-toggle="dropdown">Side Panels <b className="caret"></b></a>
        <ul className="dropdown-menu">
          <BootstrapDropdownToggleItem
            handleClick={this.props.toggleHashtagPanelVisibility}
            checked={this.props.hashtagPanelVisible}>Social Panel</BootstrapDropdownToggleItem>
          <BootstrapDropdownToggleItem
            handleClick={this.props.toggleChatPanelVisibility}
            checked={this.props.chatPanelVisible}>Chat Panel</BootstrapDropdownToggleItem>
        </ul>
      </li>
    )
  }
})

export default SettingsDropdown
