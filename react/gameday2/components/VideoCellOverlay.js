import React, { PropTypes } from 'react'
import { Tooltip, OverlayTrigger } from 'react-bootstrap'
import WebcastSelectionPanel from './WebcastSelectionPanel'
import SwapPanel from './SwapPanel'
const classNames = require('classnames')

const VideoCellOverlay = React.createClass({
  propTypes: {
    mouseOverContainer: PropTypes.bool.isRequired,
    webcast: PropTypes.object.isRequired,
    location: PropTypes.number.isRequired,
  },
  getInitialState() {
    return {
      showWebcastSelectionPanel: false,
      showSwapPanel: false,
    }
  },
  onCloseClicked() {
    this.props.removeWebcast(this.props.webcast.id)
  },
  showWebcastSelectionPanel() {
    this.setState({ showWebcastSelectionPanel: true })
  },
  hideWebcastSelectionPanel() {
    this.setState({ showWebcastSelectionPanel: false })
  },
  showSwapPanel() {
    this.setState({ showSwapPanel: true })
  },
  hideSwapPanel() {
    this.setState({ showSwapPanel: false })
  },
  webcastSelected(webcastId) {
    this.props.addWebcastAtLocation(webcastId, this.props.location)
    this.hideWebcastSelectionPanel()
  },
  handleSwap(destinationLocation) {
    this.props.swapWebcasts(this.props.location, destinationLocation)
    this.hideSwapPanel()
  },
  shouldShow() {
    return (this.props.mouseOverContainer || this.isOverlayExpanded())
  },
  isOverlayExpanded() {
    return this.state.showWebcastSelectionPanel || this.state.showSwapPanel
  },
  render() {
    let classes = classNames({
      'hidden': !this.shouldShow(),
      'panel': true,
      'panel-default': true,
      'video-cell-overlay': true,
      'expanded': this.isOverlayExpanded(),
    })
    if (this.props.webcast) {
      const closeTooltip = (<Tooltip id="closeTooltip">Close webcast</Tooltip>)
      const changeWebcastTooltip = (<Tooltip id="changeWebcastTooltip">Change webcast</Tooltip>)
      const swapWebcastTooltip = (<Tooltip id="swapWebcastTooltip">Swap webcast position</Tooltip>)
      return (
        <div className={classes}>
          <div className="panel-heading">
            <h3 className="panel-title">{this.props.webcast.name}</h3>
            <div className="overlay-button-container">
              <OverlayTrigger placement="bottom" overlay={swapWebcastTooltip}>
                <i className="material-icons overlay-button" onClick={this.showSwapPanel}>compare_arrows</i>
              </OverlayTrigger>
              <OverlayTrigger placement="bottom" overlay={changeWebcastTooltip}>
                <i className="material-icons overlay-button" onClick={this.showWebcastSelectionPanel}>videocam</i>
              </OverlayTrigger>
              <OverlayTrigger placement="bottom" overlay={closeTooltip}>
                <i className="material-icons overlay-button button-close" onClick={this.onCloseClicked}>close</i>
              </OverlayTrigger>
            </div>
          </div>
          <WebcastSelectionPanel
            webcasts={this.props.webcasts}
            webcastsById={this.props.webcastsById}
            displayedWebcasts={this.props.displayedWebcasts}
            enabled={this.state.showWebcastSelectionPanel}
            webcastSelected={this.webcastSelected}
            closeWebcastSelectionPanel={this.hideWebcastSelectionPanel}
          />
          <SwapPanel
            location={this.props.location}
            layoutId={this.props.layoutId}
            enabled={this.state.showSwapPanel}
            close={this.hideSwapPanel}
            swapToLocation={this.handleSwap}
          />
        </div>
      )
    }
  },
})

export default VideoCellOverlay
