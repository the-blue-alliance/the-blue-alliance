import React, { PropTypes } from 'react'
import BootstrapDropdownToggleItem from './BootstrapDropdownToggleItem'

var SettingsDropdown = React.createClass({
  propTypes: {
    toggleChatSidebarVisibility: PropTypes.func.isRequired,
    toggleHashtagSidebarVisibility: PropTypes.func.isRequired,
    chatSidebarVisible: PropTypes.bool.isRequired,
    hashtagSidebarVisible: PropTypes.bool.isRequired
  },
  toggleHashtagSidebarVisibility: function(e) {
    if (this.props.toggleHashtagSidebarVisibility) {
      e.preventDefault()
      e.stopPropagation()
      this.props.toggleHashtagSidebarVisibility()
    }
  },
  toggleChatSidebarVisibility: function(e) {
    if (this.props.toggleChatSidebarVisibility) {
      e.preventDefault()
      e.stopPropagation()
      this.props.togglechatSidebarVisibility()
    }
  },
  render: function() {
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle" data-toggle="dropdown">Side Panels <b className="caret"></b></a>
        <ul className="dropdown-menu">
          <BootstrapDropdownToggleItem
            handleClick={this.props.toggleHashtagSidebarVisibility}
            checked={this.props.hashtagSidebarVisible}>Social Panel</BootstrapDropdownToggleItem>
          <BootstrapDropdownToggleItem
            handleClick={this.props.toggleChatSidebarVisibility}
            checked={this.props.chatSidebarVisible}>Chat Panel</BootstrapDropdownToggleItem>
        </ul>
      </li>
    )
  }
})

export default SettingsDropdown
