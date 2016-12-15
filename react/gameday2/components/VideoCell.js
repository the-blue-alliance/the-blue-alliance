import React, { PropTypes } from 'react'
import classNames from 'classnames'
import WebcastSelectionPanel from './WebcastSelectionPanel'
import EmbedUstream from './EmbedUstream'
import EmbedYoutube from './EmbedYoutube'
import EmbedTwitch from './EmbedTwitch'
import VideoCellToolbarContainer from '../containers/VideoCellToolbarContainer'
import WebcastSelectionOverlayDialogContainer from '../containers/WebcastSelectionOverlayDialogContainer'
import { WebcastPropType } from '../utils/webcastUtils'
import RaisedButton from 'material-ui/RaisedButton'

const VideoCell = React.createClass({
  propTypes: {
    webcast: WebcastPropType,
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    displayedWebcasts: PropTypes.array.isRequired,
    location: PropTypes.number.isRequired,
    addWebcastAtLocation: PropTypes.func.isRequired,
  },
  getInitialState() {
    return {
      webcastSelectionDialogOpen: false,
    }
  },
  onRequestOpenWebcastSelectionDialog() {
    this.setState({ webcastSelectionDialogOpen: true })
  },
  onRequestCloseWebcastSelectionDialog() {
    this.setState({ webcastSelectionDialogOpen: false })
  },
  onWebcastSelected(webcastId) {
    this.props.addWebcastAtLocation(webcastId, this.props.location)
    this.onRequestCloseWebcastSelectionDialog()
  },
  render() {
    const classes = classNames({
      'video-cell': true,
      [`video-${this.props.location}`]: true,
    })

    if (this.props.webcast) {
      let cellEmbed
      switch (this.props.webcast.type) {
        case 'ustream':
          cellEmbed = (<EmbedUstream webcast={this.props.webcast} />)
          break
        case 'youtube':
          cellEmbed = (<EmbedYoutube webcast={this.props.webcast} />)
          break
        case 'twitch':
          cellEmbed = (<EmbedTwitch webcast={this.props.webcast} />)
          break
        default:
          cellEmbed = ''
          break
      }

      const cellStyle = {
        paddingBottom: '48px',
      }

      const toolbarStyle = {
        position: 'absolute',
        bottom: 0,
        width: '100%',
        height: '48px',
      }

      return (
        <div
          className={classes}
          style={cellStyle}
        >
          {cellEmbed}
          <VideoCellToolbarContainer
            style={toolbarStyle}
            webcast={this.props.webcast}
            onRequestOpenWebcastSelectionDialog={() => this.onRequestOpenWebcastSelectionDialog()}
          />
          <WebcastSelectionOverlayDialogContainer
            open={this.state.webcastSelectionDialogOpen}
            webcast={this.props.webcast}
            onRequestClose={this.onRequestCloseWebcastSelectionDialog}
            onWebcastSelected={this.onWebcastSelected}
          />
        </div>
      )
    }

    const emptyContainerStyle = {
      width: '100%',
      height: '100%',
    }

    const centerButtonStyle = {
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translateX(-50%) translateY(-50%)',
    }

    return (
      <div className={classes} >
        <div style={emptyContainerStyle}>
          <RaisedButton
            label="Select a webcast"
            style={centerButtonStyle}
            onTouchTap={this.onRequestOpenWebcastSelectionDialog}
          />
        </div>
        <WebcastSelectionOverlayDialogContainer
          open={this.state.webcastSelectionDialogOpen}
          webcast={this.props.webcast}
          onRequestClose={this.onRequestCloseWebcastSelectionDialog}
          onWebcastSelected={this.onWebcastSelected}
        />
      </div>
  )
  },
})

export default VideoCell
