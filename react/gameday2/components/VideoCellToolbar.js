import React, { PropTypes } from 'react'
import { Toolbar, ToolbarGroup, ToolbarTitle } from 'material-ui/Toolbar'
import IconButton from 'material-ui/IconButton'
import SvgIcon from 'material-ui/SvgIcon'
import CloseIcon from 'material-ui/svg-icons/navigation/close'
import SwapIcon from 'material-ui/svg-icons/action/compare-arrows'
import VideocamIcon from 'material-ui/svg-icons/av/videocam'
import { white, grey900 } from 'material-ui/styles/colors'

export default class VideoCellToolbar extends React.Component {

  static propTypes = {
    webcast: PropTypes.object.isRequired,
  }

  render() {

    const toolbarStyle = {
      backgroundColor: grey900,
      ...this.props.style,
    }

    const titleStyle = {
      color: white,
      fontSize: 16,
    }

    return (
      <Toolbar style={toolbarStyle}>
        <ToolbarGroup>
          <ToolbarTitle
            text={this.props.webcast.name}
            style={titleStyle}
          />
        </ToolbarGroup>
        <ToolbarGroup lastChild>
          <IconButton
            tooltip="Swap position"
            tooltipPosition="top-center"
            touch
          >
            <SwapIcon color={white} />
          </IconButton>
          <IconButton
            tooltip="Change webcast"
            tooltipPosition="top-center"
            touch
          >
            <VideocamIcon color={white} />
          </IconButton>
          <IconButton
            onTouchTap={() => this.props.removeWebcast(this.props.webcast.id)}
            tooltip="Close webcast"
            tooltipPosition="top-left"
            touch
          >
            <CloseIcon color={white} />
          </IconButton>
        </ToolbarGroup>
      </Toolbar>
    )
  }
}
