import React, { PropTypes } from 'react'
import BootstrapButton from './BootstrapButton'
import SettingsDropdown from './SettingsDropdown'
import SidebarToggleDropdown from './SidebarToggleDropdown'
import LayoutDropdown from './LayoutDropdown'
import classNames from 'classnames'

export default React.createClass({
  propTypes: {
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    hashtagSidebarVisible: PropTypes.bool.isRequired,
    chatSidebarVisible: PropTypes.bool.isRequired,
    addWebcast: PropTypes.func.isRequired,
    resetWebcasts: PropTypes.func.isRequired,
    toggleHashtagSidebarVisibility: PropTypes.func.isRequired,
    toggleChatSidebarVisibility: PropTypes.func.isRequired,
    setLayout: PropTypes.func.isRequired,
  },
  render() {
    return (
      <nav className="navbar navbar-default navbar-fixed-top" role="navigation">
        <div className="container-fluid">
          <div className="navbar-header">
            <button type="button" className="navbar-toggle" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
              <span className="sr-only">Toggle navigation</span>
              <span className="icon-bar"></span>
              <span className="icon-bar"></span>
              <span className="icon-bar"></span>
            </button>
            <span className="navbar-brand">Gameday</span>
          </div>

          <div className="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
            <ul className="nav navbar-nav navbar-right">
              <LayoutDropdown setLayout={this.props.setLayout} />
              <SidebarToggleDropdown
                toggleChatSidebarVisibility={this.props.toggleChatSidebarVisibility}
                toggleHashtagSidebarVisibility={this.props.toggleHashtagSidebarVisibility}
                chatSidebarVisible={this.props.chatSidebarVisible}
                hashtagSidebarVisible={this.props.hashtagSidebarVisible}
              />
              <SettingsDropdown resetWebcasts={this.props.resetWebcasts} />
            </ul>
          </div>
        </div>
      </nav>
    )
  },
})
