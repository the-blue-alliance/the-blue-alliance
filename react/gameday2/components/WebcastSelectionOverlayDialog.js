import React, { PropTypes } from 'react'
import Paper from 'material-ui/Paper'
import FlatButton from 'material-ui/FlatButton'
import List from 'material-ui/List'
import EventListener from 'react-event-listener'
import WebcastSelectionOverlayDialogItem from './WebcastSelectionOverlayDialogItem'
import { webcastPropType } from '../utils/webcastUtils'

export default class VideoCellOverlayDialog extends React.Component {

  static propTypes = {
    open: PropTypes.bool.isRequired,
    webcasts: PropTypes.arrayOf(PropTypes.string).isRequired,
    webcastsById: PropTypes.objectOf(webcastPropType).isRequired,
    displayedWebcasts: PropTypes.arrayOf(PropTypes.string).isRequired,
    onWebcastSelected: PropTypes.func.isRequired,
    onRequestClose: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props)

    this.layout = {
      dialogMargin: 20,
    }
  }

  componentDidMount() {
    this.updateSizing()
  }

  componentDidUpdate() {
    this.updateSizing()
  }

  onRequestClose() {
    if (this.props.onRequestClose) {
      this.props.onRequestClose()
    }
  }

  updateSizing() {
    if (this.props.open) {
      const component = this.component
      const dialogListContainer = this.dialogListContainer
      const dialogList = this.dialogList

      let dialogHeight = 0
      dialogHeight += dialogListContainer.previousSibling.offsetHeight
      dialogHeight += dialogListContainer.nextSibling.offsetHeight
      dialogHeight += dialogList.offsetHeight

      const maxHeight = component.offsetHeight - (2 * this.layout.dialogMargin)
      if (dialogHeight > maxHeight) {
        dialogListContainer.style.overflowY = 'auto'
        let listContainerHeight = maxHeight
        listContainerHeight -= dialogListContainer.previousSibling.offsetHeight
        listContainerHeight -= dialogListContainer.nextSibling.offsetHeight
        dialogListContainer.style.height = `${listContainerHeight}px`
      } else {
        dialogListContainer.style.height = null
      }
    }
  }

  render() {
    const wrapperStyle = {
      position: 'absolute',
      top: 0,
      bottom: 0,
      left: 0,
      right: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.541176)',
    }

    const paperStyle = {
      margin: this.layout.dialogMargin,
      width: 'calc(100% - 40px)',
      maxWidth: '400px',
      marginLeft: 'auto',
      marginRight: 'auto',
      position: 'relative',
    }

    const titleStyle = {
      padding: '16px',
      fontSize: '22px',
      margin: 0,
      fontWeight: 400,
      borderBottom: '1px solid rgb(224, 224, 224)',
    }

    const buttonContainerStyle = {
      padding: '8px',
      width: '100%',
      textAlign: 'right',
      borderTop: '1px solid rgb(224, 224, 224)',
    }

    const listContainerStyle = {
      overflowY: 'auto',
    }

    const buttonContainerElement = (
      <div style={buttonContainerStyle}>
        <FlatButton
          label="Cancel"
          onTouchTap={() => this.onRequestClose()}
        />
      </div>
    )

    // Construct list of webcasts
    const webcastItems = []
    // Don't let the user choose a webcast that is already displayed elsewhere
    const availableWebcasts = this.props.webcasts.filter((webcastId) => this.props.displayedWebcasts.indexOf(webcastId) === -1)
    availableWebcasts.forEach((webcastId) => {
      const webcast = this.props.webcastsById[webcastId]
      webcastItems.push(
        <WebcastSelectionOverlayDialogItem
          key={webcast.id}
          webcast={webcast}
          webcastSelected={this.props.onWebcastSelected}
        />
      )
    })

    if (this.props.open) {
      // This "div" soup is needed because React is deprecating the ability to
      // access the DOM nodes of components, so we need to wrap them in divs in
      // order to measure and size them. See https://github.com/yannickcr/eslint-plugin-react/issues/678
      return (
        <div
          style={wrapperStyle}
          onTouchTap={() => this.onRequestClose()}
          ref={(e) => { this.component = e }}
        >
          <EventListener
            target="window"
            onResize={() => this.updateSizing()}
          />
          <Paper
            style={paperStyle}
            zDepth={5}
            onTouchTap={(e) => e.stopPropagation()}
          >
            <h3 style={titleStyle}>Select a webcast</h3>
            <div
              style={listContainerStyle}
              ref={(e) => { this.dialogListContainer = e }}
            >
              <div ref={(e) => { this.dialogList = e }}>
                <List>
                  {webcastItems}
                </List>
              </div>
            </div>
            {buttonContainerElement}
          </Paper>
        </div>
      )
    }

    return null
  }
}
