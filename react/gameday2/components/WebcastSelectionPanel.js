import React, { PropTypes } from 'react'
import WebcastSelectionPanelItem from './WebcastSelectionPanelItem'
var classNames = require('classnames')

var WebcastSelectionPanel = React.createClass({
  propTypes: {
    enabled: PropTypes.bool.isRequired,
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    displayedWebcasts: PropTypes.array.isRequired,
    webcastSelected: PropTypes.func.isRequired,
    closeWebcastSelectionPanel: PropTypes.func.isRequired
  },
  render: function() {
    // Construct list of webcasts
    let webcastItems = []
    // Don't let the user choose a webcast that is already displayed elsewhere
    let availableWebcasts = this.props.webcasts.filter((webcastId) => this.props.displayedWebcasts.indexOf(webcastId) == -1)
    for (let webcastId of availableWebcasts) {
      let webcast = this.props.webcastsById[webcastId]
      webcastItems.push(
        <WebcastSelectionPanelItem
          key={webcast.id}
          webcast={webcast}
          webcastSelected={this.props.webcastSelected} />
      )
    }

    var classes = classNames({
      'hidden': !this.props.enabled,
      'webcast-selection-panel': true
    })

    return (
      <div className={classes}>
        <a className="button-close" href="#" onClick={this.props.closeWebcastSelectionPanel}>
          <span className="glyphicon glyphicon-remove"></span>
        </a>
        <div className="list-group">
          <h3>Select a Webcast</h3>
          {webcastItems}
        </div>
      </div>
    )
  }
})

export default WebcastSelectionPanel
