import React, { PropTypes } from 'react'
import WebcastSelectionPanelItem from './WebcastSelectionPanelItem'
var classNames = require('classnames')

var WebcastSelectionPanel = React.createClass({
  propTypes: {
    enabled: PropTypes.bool.isRequired,
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    webcastSelected: PropTypes.func.isRequired,
    closeWebcastSelectionPanel: PropTypes.func.isRequired
  },
  render: function() {
    // Construct list of webcasts
    let webcastItems = []
    for (let webcastId of this.props.webcasts) {
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
