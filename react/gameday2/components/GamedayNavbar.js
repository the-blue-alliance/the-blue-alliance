import React, { PropTypes } from 'react'
import SettingsDropdown from './SettingsDropdown'
import SidebarToggleDropdown from './SidebarToggleDropdown'
import LayoutDropdown from './LayoutDropdown'

const GamedayNavbar = (props) => (
  <nav className="navbar navbar-default navbar-fixed-top" role="navigation">
    <div className="container-fluid">
      <div className="navbar-header">
        <button type="button" className="navbar-toggle" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
          <span className="sr-only">Toggle navigation</span>
          <span className="icon-bar" />
          <span className="icon-bar" />
          <span className="icon-bar" />
        </button>
        <span className="navbar-brand">Gameday</span>
      </div>

      <div className="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
        <ul className="nav navbar-nav navbar-right">
          <LayoutDropdown setLayout={props.setLayout} />
          <SidebarToggleDropdown
            toggleChatSidebarVisibility={props.toggleChatSidebarVisibility}
            toggleHashtagSidebarVisibility={props.toggleHashtagSidebarVisibility}
            chatSidebarVisible={props.chatSidebarVisible}
            hashtagSidebarVisible={props.hashtagSidebarVisible}
          />
          <SettingsDropdown resetWebcasts={props.resetWebcasts} />
        </ul>
      </div>
    </div>
  </nav>
)

GamedayNavbar.propTypes = {
  webcasts: PropTypes.array.isRequired,
  webcastsById: PropTypes.object.isRequired,
  hashtagSidebarVisible: PropTypes.bool.isRequired,
  chatSidebarVisible: PropTypes.bool.isRequired,
  addWebcast: PropTypes.func.isRequired,
  resetWebcasts: PropTypes.func.isRequired,
  toggleHashtagSidebarVisibility: PropTypes.func.isRequired,
  toggleChatSidebarVisibility: PropTypes.func.isRequired,
  setLayout: PropTypes.func.isRequired,
}

export default GamedayNavbar
