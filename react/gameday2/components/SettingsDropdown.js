import React from 'react'
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem'

export default React.createClass({
  render() {
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle navbar-icon" data-toggle="dropdown"><i className="material-icons">settings</i></a>
        <ul className="dropdown-menu">
          <BootstrapNavDropdownListItem handleClick={this.props.resetWebcasts}>Reset Layout</BootstrapNavDropdownListItem>
          <li className="divider"></li>
          <BootstrapNavDropdownListItem
            data_toggle="modal"
            data_target="#followingTeamsModal"
          >Follow Teams</BootstrapNavDropdownListItem>
          <li className="divider"></li>
          <BootstrapNavDropdownListItem>Debug Menu</BootstrapNavDropdownListItem>
          <BootstrapNavDropdownListItem>TODO Show Beeper</BootstrapNavDropdownListItem>
        </ul>
      </li>
    )
  },
})
