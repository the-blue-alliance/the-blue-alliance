import React, { PropTypes } from 'react'
import classNames from 'classnames'
import WebcastSelectionPanelItem from './WebcastSelectionPanelItem'

const WebcastSelectionPanel = (props) => {
    // Construct list of webcasts
  let webcastItems = []
    // Don't let the user choose a webcast that is already displayed elsewhere
  const availableWebcasts = props.webcasts.filter((webcastId) => props.displayedWebcasts.indexOf(webcastId) === -1)
  for (const webcastId of availableWebcasts) {
    let webcast = props.webcastsById[webcastId]
    webcastItems.push(
      <WebcastSelectionPanelItem
        key={webcast.id}
        webcast={webcast}
        webcastSelected={this.props.webcastSelected}
      />
    )
  }

  let classes = classNames({
    hidden: !props.enabled,
    'webcast-selection-panel': true,
  })

  return (
    <div className={classes}>
      <button
        type="button"
        className="button-close btn btn-sm btn-default"
        href="#"
        onClick={props.closeWebcastSelectionPanel}
      >
        <span className="glyphicon glyphicon-remove" />
      </button>
      <div className="list-group">
        <h3>Select a Webcast</h3>
        {webcastItems}
      </div>
    </div>
  )
}

WebcastSelectionPanel.propTypes = {
  enabled: PropTypes.bool.isRequired,
  webcasts: PropTypes.array.isRequired,
  webcastsById: PropTypes.object.isRequired,
  displayedWebcasts: PropTypes.array.isRequired,
  webcastSelected: PropTypes.func.isRequired,
  closeWebcastSelectionPanel: PropTypes.func.isRequired,
}

export default WebcastSelectionPanel
