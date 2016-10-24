import React, { PropTypes } from 'react'
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem'

const SettingsDropdown = (props) => (
  <li className="dropdown">
    <a href="#" className="dropdown-toggle navbar-icon" data-toggle="dropdown"><i className="material-icons">settings</i></a>
    <ul className="dropdown-menu">
      <BootstrapNavDropdownListItem handleClick={props.resetWebcasts}>Reset Layout</BootstrapNavDropdownListItem>
      <li className="divider" />
      <BootstrapNavDropdownListItem
        data_toggle="modal"
        data_target="#followingTeamsModal"
      >Follow Teams</BootstrapNavDropdownListItem>
      <li className="divider" />
      <BootstrapNavDropdownListItem>Debug Menu</BootstrapNavDropdownListItem>
      <BootstrapNavDropdownListItem>TODO Show Beeper</BootstrapNavDropdownListItem>
    </ul>
  </li>
)

SettingsDropdown.propTypes = {
  resetWebcasts: PropTypes.func,
}

export default SettingsDropdown
