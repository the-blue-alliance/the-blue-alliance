import React, { PropTypes } from 'react'
import Paper from 'material-ui/Paper'
import FlatButton from 'material-ui/FlatButton'
import List from 'material-ui/List'
import WebcastSelectionOverlayDialogItem from './WebcastSelectionOverlayDialogItem'

export default class VideoCellOverlayDialog extends React.Component {

  static propTypes = {
    open: PropTypes.bool.isRequired,
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    displayedWebcasts: PropTypes.array.isRequired,
    webcastSelected: PropTypes.func.isRequired,
    onRequestClose: PropTypes.func.isRequired,
  }

  onRequestClose() {
    if (this.props.onRequestClose) {
      this.props.onRequestClose();
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
      margin: 20,
      width: 'calc(100% - 40px)',
      maxWidth: '400px',
      height: '400px',
      maxHeight: 'calc(100% - 40px)',
      marginLeft: 'auto',
      marginRight: 'auto',
      position: 'relative',
    }

    const titleStyle = {
      padding: '24px 24px 20px',
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
      position: 'absolute',
      bottom: 0,
    }

    const buttonContainerElement = (
      <div style={buttonContainerStyle}>
        <FlatButton
          label="Cancel"
          onTouchTap={() => this.onRequestClose()} />
      </div>
    )

    // Construct list of webcasts
    const webcastItems = []
    // Don't let the user choose a webcast that is already displayed elsewhere
    const availableWebcasts = this.props.webcasts.filter((webcastId) => this.props.displayedWebcasts.indexOf(webcastId) === -1)
    for (const webcastId of availableWebcasts) {
      const webcast = this.props.webcastsById[webcastId]
      webcastItems.push(
        <WebcastSelectionOverlayDialogItem
          key={webcast.id}
          webcast={webcast}
          webcastSelected={this.props.webcastSelected}
        />
      )
    }

    if (this.props.open) {
      return (
        <div style={wrapperStyle}>
          <Paper style={paperStyle} zDepth={5}>
            <h3 style={titleStyle}>Select a webcast</h3>
            <List>
              {webcastItems}
            </List>
            {buttonContainerElement}
          </Paper>
        </div>
      )
    }

    return null;
  }
}
