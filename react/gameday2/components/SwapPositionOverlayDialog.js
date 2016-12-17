import React, { PropTypes } from 'react'
import Paper from 'material-ui/Paper'
import FlatButton from 'material-ui/FlatButton'
import EventListener from 'react-event-listener'
import SwapPositionPreviewCell from './SwapPositionPreviewCell'
import { NUM_VIEWS_FOR_LAYOUT, LAYOUT_STYLES } from '../constants/LayoutConstants'

function getStyles() {
  const styles = {
    wrapperStyle: {
      position: 'absolute',
      top: 0,
      bottom: 0,
      left: 0,
      right: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.541176)',
    },
    containerStyle: {
      width: '100%',
      position: 'absolute',
      top: 0,
      bottom: 0,
    },
    paperStyle: {
      width: 'calc(100% - 40px)',
      height: 'calc(100% - 40px)',
      margin: '20px',
      position: 'relative',
    },
    titleStyle: {
      padding: '16px',
      fontSize: '22px',
      margin: 0,
      fontWeight: 400,
      borderBottom: '1px solid rgb(224, 224, 224)',
    },
    contentStyle: {
      position: 'absolute',
      width: '100%',
    },
    buttonContainerStyle: {
      padding: '8px',
      width: '100%',
      textAlign: 'right',
      position: 'absolute',
      bottom: 0,
      borderTop: '1px solid rgb(224, 224, 224)',
    },
    previewContainerStyle: {
      padding: '4px',
    },
  }

  return styles
}

export default class SwapPositionOverlayDialog extends React.Component {
  static propTypes = {
    open: PropTypes.bool.isRequired,
    location: PropTypes.number.isRequired,
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
    this.props.swapWebcasts(this.props.location, targetPosition)
    this.onRequestClose()
  }

  onRequestClose() {
    if (this.props.onRequestClose) {
      this.props.onRequestClose()
    }
  }

  updateSizing() {
    if (this.props.open) {
      const dialogContainer = this.dialogContainer
      const dialogContent = this.dialogContent

      let minHeight = 0
      minHeight += dialogContent.previousSibling.offsetHeight
      minHeight += dialogContent.nextSibling.offsetHeight

      const dialogHeight = dialogContainer.offsetHeight

      dialogContent.style.top = `${dialogContent.previousSibling.offsetHeight}px`
      dialogContent.style.bottom = `${dialogContent.nextSibling.offsetHeight}px`

      if (dialogHeight < minHeight) {
        dialogContainer.style.height = `${minHeight}px`
      } else {
        dialogContainer.style.height = null
      }
    }
  }

  render() {
    if (this.props.open) {
      const styles = getStyles()

      const videoViews = []
      const layoutId = this.props.layoutId

      for (let i = 0; i < NUM_VIEWS_FOR_LAYOUT[layoutId]; i++) {
        const cellStyle = LAYOUT_STYLES[layoutId][i]

        videoViews.push(
          <SwapPositionPreviewCell
            key={i.toString()}
            style={cellStyle}
            enabled={i !== this.props.location}
            onClick={() => this.onRequestSwap(i)}
          />
        )
      }

      const buttonContainerElement = (
        <div style={styles.buttonContainerStyle}>
          <FlatButton
            label="Cancel"
            onTouchTap={() => this.onRequestClose()}
          />
        </div>
      )

      // This "div" soup is needed because React is deprecating the ability to
      // access the DOM nodes of components, so we need to wrap them in divs in
      // order to measure and size them. See https://github.com/yannickcr/eslint-plugin-react/issues/678
      return (
        <div
          style={styles.wrapperStyle}
          onTouchTap={() => this.onRequestClose()}
          ref={e => { this.component = e }}
        >
          <EventListener
            target="window"
            onResize={() => this.updateSizing()}
          />
          <div
            ref={e => { this.dialogContainer = e }}
            style={styles.containerStyle}
          >
            <Paper
              style={styles.paperStyle}
              zDepth={5}
              onTouchTap={e => e.stopPropagation()}
            >
              <h3 style={styles.titleStyle}>Select a position to swap with</h3>
              <div
                ref={e => { this.dialogContent = e }}
                style={styles.contentStyle}
              >
                <div style={styles.previewContainerStyle}>
                  {videoViews}
                </div>
              </div>
              {buttonContainerElement}
            </Paper>
          </div>
        </div>
      )
    }

    return null
  }
}
