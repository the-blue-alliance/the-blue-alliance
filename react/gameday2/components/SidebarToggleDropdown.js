import React, { PropTypes } from 'react'
import BootstrapDropdownToggleItem from './BootstrapDropdownToggleItem'

const SettingsDropdown = React.createClass({
  propTypes: {
    toggleChatSidebarVisibility: PropTypes.func.isRequired,
    toggleHashtagSidebarVisibility: PropTypes.func.isRequired,
    chatSidebarVisible: PropTypes.bool.isRequired,
    hashtagSidebarVisible: PropTypes.bool.isRequired,
  },
  toggleHashtagSidebarVisibility(e) {
    if (this.props.toggleHashtagSidebarVisibility) {
      e.preventDefault()
      e.stopPropagation()
      this.props.toggleHashtagSidebarVisibility()
    }
  },
  toggleChatSidebarVisibility(e) {
    if (this.props.toggleChatSidebarVisibility) {
      e.preventDefault()
      e.stopPropagation()
      this.props.togglechatSidebarVisibility()
    }
  },
  render() {
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle" data-toggle="dropdown">Sidebars <b className="caret"></b></a>
        <ul className="dropdown-menu">
          <BootstrapDropdownToggleItem
            handleClick={this.props.toggleHashtagSidebarVisibility}
            checked={this.props.hashtagSidebarVisible}
          >Social</BootstrapDropdownToggleItem>
          <BootstrapDropdownToggleItem
            handleClick={this.props.toggleChatSidebarVisibility}
            checked={this.props.chatSidebarVisible}
          >Chat</BootstrapDropdownToggleItem>
        </ul>
      </li>
    )
  },
})

export default SettingsDropdown
