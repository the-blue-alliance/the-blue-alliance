import React, { PropTypes } from 'react'
import Dialog from 'material-ui/Dialog'
import { green500, indigo500 } from 'material-ui/styles/colors'
import Divider from 'material-ui/Divider'
import FlatButton from 'material-ui/FlatButton'
import { List, ListItem } from 'material-ui/List'
import Subheader from 'material-ui/Subheader'
import ActionGrade from 'material-ui/svg-icons/action/grade'
import ActionHelp from 'material-ui/svg-icons/action/help'
import VideoCam from 'material-ui/svg-icons/av/videocam'
import VideoCamOff from 'material-ui/svg-icons/av/videocam-off'
import WebcastSelectionDialogItem from './WebcastSelectionDialogItem'
import { webcastPropType } from '../utils/webcastUtils'

export default class WebcastSelectionDialog extends React.Component {
  static propTypes = {
    open: PropTypes.bool.isRequired,
    webcasts: PropTypes.arrayOf(PropTypes.string).isRequired,
    webcastsById: PropTypes.objectOf(webcastPropType).isRequired,
    specialWebcastIds: PropTypes.any.isRequired, // Can't figure out how to check for Set()
    displayedWebcasts: PropTypes.arrayOf(PropTypes.string).isRequired,
    onWebcastSelected: PropTypes.func.isRequired,
    onRequestClose: PropTypes.func.isRequired,
  }

  onRequestClose() {
    if (this.props.onRequestClose) {
      this.props.onRequestClose()
    }
  }

  render() {
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
    const availableWebcasts = this.props.webcasts.filter(
      (webcastId) => this.props.displayedWebcasts.indexOf(webcastId) === -1
    )
    availableWebcasts.forEach((webcastId) => {
      const webcast = this.props.webcastsById[webcastId]

      let rightIcon = <ActionHelp />
      let secondaryText = null
      if (webcast.status === 'online') {
        rightIcon = (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              width: 96,
            }}
          >
            {webcast.viewerCount && (
              <small
                style={{
                  textAlign: 'center',
                  marginRight: 8,
                }}
              >
                {webcast.viewerCount.toLocaleString()}
                <br />
                Viewers
              </small>
            )}
            <VideoCam color={green500} />
          </div>
        )
        if (webcast.streamTitle) {
          secondaryText = webcast.streamTitle
        }
      } else if (webcast.status === 'offline') {
        rightIcon = <VideoCamOff />
      }

      if (this.props.specialWebcastIds.has(webcast.id)) {
        const item = (
          <WebcastSelectionDialogItem
            key={webcast.id}
            webcast={webcast}
            webcastSelected={this.props.onWebcastSelected}
            secondaryText={secondaryText}
            rightIcon={rightIcon}
          />
        )
        if (webcast.status === 'offline') {
          offlineSpecialWebcastItems.push(item)
        } else {
          specialWebcastItems.push(item)
        }
      } else if (webcast.id.startsWith('bluezone')) {
        bluezoneWebcastItems.push(
          <WebcastSelectionDialogItem
            key={webcast.id}
            webcast={webcast}
            webcastSelected={this.props.onWebcastSelected}
            secondaryText={'The best matches from across FRC'}
            rightIcon={<ActionGrade color={indigo500} />}
          />
        )
      } else {
        const item = (
          <WebcastSelectionDialogItem
            key={webcast.id}
            webcast={webcast}
            webcastSelected={this.props.onWebcastSelected}
            secondaryText={secondaryText}
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
        <Subheader key="specialWebcastsHeader" style={subheaderStyle}>
          Special Webcasts
        </Subheader>
      )
      allWebcastItems = allWebcastItems.concat(bluezoneWebcastItems)
      allWebcastItems = allWebcastItems.concat(specialWebcastItems)
    }
    if (webcastItems.length !== 0) {
      if (specialWebcastItems.length !== 0) {
        allWebcastItems.push(<Divider key="eventWebcastsDivider" />)
      }
      allWebcastItems.push(
        <Subheader key="eventWebcastsHeader" style={subheaderStyle}>
          Event Webcasts
        </Subheader>
      )
      allWebcastItems = allWebcastItems.concat(webcastItems)
    }
    if (offlineWebcastItems.length !== 0) {
      if (webcastItems.length !== 0) {
        allWebcastItems.push(<Divider key="offlineEventWebcastsDivider" />)
      }
      allWebcastItems.push(
        <Subheader key="offlineWebcastsHeader" style={subheaderStyle}>
          Offline Event Webcasts
        </Subheader>
      )
      allWebcastItems = allWebcastItems.concat(offlineWebcastItems)
    }
    if (offlineSpecialWebcastItems.length !== 0) {
      if (offlineWebcastItems.length !== 0) {
        allWebcastItems.push(<Divider key="offlineSpecialWebcastsDivider" />)
      }
      allWebcastItems.push(
        <Subheader key="offlineSpecialWebcastsHeader" style={subheaderStyle}>
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

    const actions = [
      <FlatButton
        label="Cancel"
        onTouchTap={() => this.onRequestClose()}
        primary
      />,
    ]

    const titleStyle = {
      padding: 16,
    }

    const bodyStyle = {
      padding: 0,
    }

    return (
      <Dialog
        title="Select a webcast"
        actions={actions}
        modal={false}
        titleStyle={titleStyle}
        bodyStyle={bodyStyle}
        open={this.props.open}
        onRequestClose={() => this.onRequestClose()}
        autoScrollBodyContent
      >
        <List>{allWebcastItems}</List>
      </Dialog>
    )
  }
}
