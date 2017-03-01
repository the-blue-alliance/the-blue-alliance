import React, { PropTypes } from 'react'
import Paper from 'material-ui/Paper'
import { green500, indigo500 } from 'material-ui/styles/colors'
import Divider from 'material-ui/Divider'
import FlatButton from 'material-ui/FlatButton'
import { List, ListItem } from 'material-ui/List'
import Subheader from 'material-ui/Subheader'
import ActionGrade from 'material-ui/svg-icons/action/grade'
import ActionHelp from 'material-ui/svg-icons/action/help'
import VideoCam from 'material-ui/svg-icons/av/videocam'
import VideoCamOff from 'material-ui/svg-icons/av/videocam-off'
import EventListener from 'react-event-listener'
import WebcastSelectionOverlayDialogItem from './WebcastSelectionOverlayDialogItem'
import { webcastPropType } from '../utils/webcastUtils'

export default class VideoCellOverlayDialog extends React.Component {

  static propTypes = {
    open: PropTypes.bool.isRequired,
    webcasts: PropTypes.arrayOf(PropTypes.string).isRequired,
    webcastsById: PropTypes.objectOf(webcastPropType).isRequired,
    specialWebcastIds: PropTypes.any.isRequired, // Can't figure out how to check for Set()
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

    const subheaderStyle = {
      color: indigo500,
    }

    // Construct list of webcasts
    const bluezoneWebcastItems = []
    const specialWebcastItems = []
    const webcastItems = []
    const offlineSpecialWebcastItems = []
    const offlineWebcastItems = []
    // Don't let the user choose a webcast that is already displayed elsewhere
    const availableWebcasts = this.props.webcasts.filter((webcastId) => this.props.displayedWebcasts.indexOf(webcastId) === -1)
    availableWebcasts.forEach((webcastId) => {
      const webcast = this.props.webcastsById[webcastId]

      let rightIcon = (<ActionHelp />)
      if (webcast.status === 'online') {
        rightIcon = (<VideoCam color={green500} />)
      } else if (webcast.status === 'offline') {
        rightIcon = (<VideoCamOff />)
      }

      if (this.props.specialWebcastIds.has(webcast.id)) {
        const item = (
          <WebcastSelectionOverlayDialogItem
            key={webcast.id}
            webcast={webcast}
            webcastSelected={this.props.onWebcastSelected}
            rightIcon={rightIcon}
          />)
        if (webcast.status === 'offline') {
          offlineSpecialWebcastItems.push(item)
        } else {
          specialWebcastItems.push(item)
        }
      } else if (webcast.id.startsWith('bluezone')) {
        bluezoneWebcastItems.push(
          <WebcastSelectionOverlayDialogItem
            key={webcast.id}
            webcast={webcast}
            webcastSelected={this.props.onWebcastSelected}
            secondaryText={'The best matches from across FRC'}
            rightIcon={<ActionGrade color={indigo500} />}
          />
        )
      } else {
        const item = (
          <WebcastSelectionOverlayDialogItem
            key={webcast.id}
            webcast={webcast}
            webcastSelected={this.props.onWebcastSelected}
            rightIcon={rightIcon}
          />
        )
        if (webcast.status === 'offline') {
          offlineWebcastItems.push(item)
        } else {
          webcastItems.push(item)
        }
      }
    })

    let allWebcastItems = []
    if (specialWebcastItems.length !== 0 || bluezoneWebcastItems.length !== 0) {
      allWebcastItems.push(
        <Subheader
          key="specialWebcastsHeader"
          style={subheaderStyle}
        >
          Special Webcasts
        </Subheader>
      )
      allWebcastItems = allWebcastItems.concat(bluezoneWebcastItems)
      allWebcastItems = allWebcastItems.concat(specialWebcastItems)
    }
    if (webcastItems.length !== 0) {
      if (specialWebcastItems.length !== 0) {
        allWebcastItems.push(
          <Divider key="eventWebcastsDivider" />
        )
      }
      allWebcastItems.push(
        <Subheader
          key="eventWebcastsHeader"
          style={subheaderStyle}
        >
          Event Webcasts
        </Subheader>
      )
      allWebcastItems = allWebcastItems.concat(webcastItems)
    }
    if (offlineWebcastItems.length !== 0) {
      if (webcastItems.length !== 0) {
        allWebcastItems.push(
          <Divider key="offlineEventWebcastsDivider" />
        )
      }
      allWebcastItems.push(
        <Subheader
          key="offlineWebcastsHeader"
          style={subheaderStyle}
        >
          Offline Event Webcasts
        </Subheader>
      )
      allWebcastItems = allWebcastItems.concat(offlineWebcastItems)
    }
    if (offlineSpecialWebcastItems.length !== 0) {
      if (offlineWebcastItems.length !== 0) {
        allWebcastItems.push(
          <Divider key="offlineSpecialWebcastsDivider" />
        )
      }
      allWebcastItems.push(
        <Subheader
          key="offlineSpecialWebcastsHeader"
          style={subheaderStyle}
        >
          Offline Special Webcasts
        </Subheader>
      )
      allWebcastItems = allWebcastItems.concat(offlineSpecialWebcastItems)
    }

    if (allWebcastItems.length === 0) {
      // No more webcasts, indicate that
      allWebcastItems.push(
        <ListItem
          key="nullWebcastsListItem"
          primaryText="No more webcasts available"
          disabled
        />
      )
    }

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
                  {allWebcastItems}
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
