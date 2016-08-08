import React, { PropTypes } from 'react'
import classNames from 'classnames'
import WebcastSelectionPanelItem from './WebcastSelectionPanelItem'

export default React.createClass({
  propTypes: {
    enabled: PropTypes.bool.isRequired,
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    displayedWebcasts: PropTypes.array.isRequired,
    webcastSelected: PropTypes.func.isRequired,
    closeWebcastSelectionPanel: PropTypes.func.isRequired,
  },
  render() {
    // Construct list of webcasts
    let webcastItems = []
    // Don't let the user choose a webcast that is already displayed elsewhere
    const availableWebcasts = this.props.webcasts.filter((webcastId) => this.props.displayedWebcasts.indexOf(webcastId) === -1)
    for (const webcastId of availableWebcasts) {
      let webcast = this.props.webcastsById[webcastId]
      webcastItems.push(
        <WebcastSelectionPanelItem
          key={webcast.id}
          webcast={webcast}
          webcastSelected={this.props.webcastSelected}
        />
      )
    }

    let classes = classNames({
      'hidden': !this.props.enabled,
      'webcast-selection-panel': true,
    })

    return (
      <div className={classes}>
        <button type="button" className="button-close btn btn-sm btn-default" href="#" onClick={this.props.closeWebcastSelectionPanel}>
          <span className="glyphicon glyphicon-remove"/>
        </button>
        <div className="list-group">
          <h3>Select a Webcast</h3>
          {webcastItems}
        </div>
      </div>
    )
  },
})
