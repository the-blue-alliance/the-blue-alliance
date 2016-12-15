import React, { PropTypes } from 'react'
import classNames from 'classnames'
import VideoOverlayContainer from '../containers/VideoOverlayContainer'
import WebcastSelectionPanel from './WebcastSelectionPanel'
import EmbedUstream from './EmbedUstream'
import EmbedYoutube from './EmbedYoutube'
import EmbedTwitch from './EmbedTwitch'
import VideoCellToolbarContainer from '../containers/VideoCellToolbarContainer'
import WebcastSelectionOverlayDialogContainer from '../containers/WebcastSelectionOverlayDialogContainer'
import { WebcastPropType } from '../utils/webcastUtils'

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
  onMouseOver() {
    this.setState({ mouseOver: true })
  },
  onMouseOut() {
    this.setState({ mouseOver: false })
  },
  onRequestOpenWebcastSelectionDialog() {
    this.setState({ webcastSelectionDialogOpen: true })
  },
  onRequestCloseWebcastSelectionDialog() {
    this.setState({ webcastSelectionDialogOpen: false })
  },
  webcastSelected(webcastId) {
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
          onMouseOver={this.onMouseOver}
          onMouseOut={this.onMouseOut}
        >
          {cellEmbed}
          <VideoOverlayContainer
            webcast={this.props.webcast}
            mouseOverContainer={this.state.mouseOver}
            location={this.props.location}
          />
          <VideoCellToolbarContainer
            style={toolbarStyle}
            webcast={this.props.webcast}
            onRequestOpenWebcastSelectionDialog={() => this.onRequestOpenWebcastSelectionDialog()}
          />
          <WebcastSelectionOverlayDialogContainer
            open={this.state.webcastSelectionDialogOpen}
            webcast={this.props.webcast}
            onRequestClose={this.onRequestCloseWebcastSelectionDialog}
          />
        </div>
      )
    }

    return (<div className={classes} >
      <div className="empty-view">
        <button type="button" className="btn btn-secondary" onClick={this.onRequestOpenWebcastSelectionDialog}>Select a webcast</button>
      </div>
      <WebcastSelectionOverlayDialogContainer
        open={this.state.webcastSelectionDialogOpen}
        webcast={this.props.webcast}
        onRequestClose={this.onRequestCloseWebcastSelectionDialog}
      />
    </div>)
  },
})

export default VideoCell
