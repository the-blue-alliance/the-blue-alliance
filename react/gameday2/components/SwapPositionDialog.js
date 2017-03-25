import React, { PropTypes } from 'react'
import Dialog from 'material-ui/Dialog'
import FlatButton from 'material-ui/FlatButton'
import EventListener from 'react-event-listener'
import SwapPositionPreviewCell from './SwapPositionPreviewCell'
import { NUM_VIEWS_FOR_LAYOUT, LAYOUT_STYLES } from '../constants/LayoutConstants'

export default class SwapPositionDialog extends React.Component {
  static propTypes = {
    open: PropTypes.bool.isRequired,
    position: PropTypes.number.isRequired,
    layoutId: PropTypes.number.isRequired,
    swapWebcasts: PropTypes.func.isRequired,
    onRequestClose: PropTypes.func.isRequired,
  }

  componentDidMount() {
    this.updateSizing()
  }

  componentDidUpdate() {
    this.updateSizing()
  }

  onRequestSwap(targetPosition) {
    this.props.swapWebcasts(this.props.position, targetPosition)
    this.onRequestClose()
  }

  onRequestClose() {
    if (this.props.onRequestClose) {
      this.props.onRequestClose()
    }
  }

  updateSizing() {
    const container = this.container
    if (this.props.open && container) {
      const windowWidth = window.innerWidth
      const windowHeight = window.innerHeight
      const aspectRatio = windowWidth / windowHeight

      const containerWidth = container.offsetWidth
      const containerHeight = containerWidth / aspectRatio

      container.style.height = `${containerHeight}px`
    }
  }

  render() {
    const videoViews = []
    const layoutId = this.props.layoutId

    for (let i = 0; i < NUM_VIEWS_FOR_LAYOUT[layoutId]; i++) {
      const cellStyle = LAYOUT_STYLES[layoutId][i]

      videoViews.push(
        <SwapPositionPreviewCell
          key={i.toString()}
          style={cellStyle}
          enabled={i !== this.props.position}
          onClick={() => this.onRequestSwap(i)}
        />
      )
    }

    const actions = [
      <FlatButton
        label="Cancel"
        primary
        onTouchTap={() => this.onRequestClose()}
      />,
    ]

    const bodyStyle = {
      padding: 8,
    }

    const previewContainerStyle = {
      padding: '4px',
      position: 'relative',
    }

    return (
      <Dialog
        title="Select a position to swap with"
        actions={actions}
        modal={false}
        bodyStyle={bodyStyle}
        open={this.props.open}
        onRequestClose={() => this.onRequestClose()}
        autoScrollBodyContent
      >
        <EventListener
          target="window"
          onResize={() => this.updateSizing()}
        />
        <div
          style={previewContainerStyle}
          ref={(e) => { this.container = e; this.updateSizing() }}
        >
          {videoViews}
        </div>
      </Dialog>
    )
  }
}
