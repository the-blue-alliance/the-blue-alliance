import React, { PropTypes } from 'react'
import BootstrapDropdownToggleItem from './BootstrapDropdownToggleItem'

const SettingsDropdown = (props) => (
  <li className="dropdown">
    <a href="#" className="dropdown-toggle" data-toggle="dropdown">Sidebars <b className="caret" /></a>
    <ul className="dropdown-menu">
      <BootstrapDropdownToggleItem
        handleClick={props.toggleHashtagSidebarVisibility}
        checked={props.hashtagSidebarVisible}
      >Social</BootstrapDropdownToggleItem>
      <BootstrapDropdownToggleItem
        handleClick={props.toggleChatSidebarVisibility}
        checked={props.chatSidebarVisible}
      >Chat</BootstrapDropdownToggleItem>
    </ul>
  </li>
)

SettingsDropdown.propTypes = {
  toggleChatSidebarVisibility: PropTypes.func.isRequired,
  toggleHashtagSidebarVisibility: PropTypes.func.isRequired,
  chatSidebarVisible: PropTypes.bool.isRequired,
  hashtagSidebarVisible: PropTypes.bool.isRequired,
}

export default SettingsDropdown
