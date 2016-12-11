import React, { PropTypes } from 'react'
import AppBar from 'material-ui/AppBar'
import FlatButton from 'material-ui/FlatButton'
import LayoutDrawer from './LayoutDrawer'

export default class GamedayNavbarMaterial extends React.Component {

  static propTypes = {
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    hashtagSidebarVisible: PropTypes.bool.isRequired,
    chatSidebarVisible: PropTypes.bool.isRequired,
    addWebcast: PropTypes.func.isRequired,
    resetWebcasts: PropTypes.func.isRequired,
    toggleHashtagSidebarVisibility: PropTypes.func.isRequired,
    setHashtagSidebarVisibility: PropTypes.func.isRequired,
    toggleChatSidebarVisibility: PropTypes.func.isRequired,
    setChatSidebarVisibility: PropTypes.func.isRequired,
    setLayout: PropTypes.func.isRequired,
    layoutId: PropTypes.number.isRequired,
    layoutSet: PropTypes.bool.isRequired,
    layoutDrawerVisible: PropTypes.bool.isRequired,
    setLayoutDrawerVisibility: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props)
  }

  render() {
    const configureLayoutButton = (
      <FlatButton
        label='Configure Layout'
        onTouchTap={() => this.props.setLayoutDrawerVisibility(true)}
      />
    )

    return (
      <div>
        <AppBar
          title='GameDay'
          showMenuIconButton={false}
          iconElementRight={configureLayoutButton}
        />
      <LayoutDrawer
        setLayout={this.props.setLayout}
        toggleChatSidebarVisibility={this.props.toggleChatSidebarVisibility}
        toggleHashtagSidebarVisibility={this.props.toggleHashtagSidebarVisibility}
        selectedLayout={this.props.layoutId}
        layoutSet={this.props.layoutSet}
        chatSidebarVisible={this.props.chatSidebarVisible}
        hashtagSidebarVisible={this.props.hashtagSidebarVisible}
        layoutDrawerVisible={this.props.layoutDrawerVisible}
        setLayoutDrawerVisibility={this.props.setLayoutDrawerVisibility}
        hasWebcasts={this.props.webcasts.length > 0}
        resetWebcasts={this.props.resetWebcasts}
      />
      </div>
    )
  }
}
