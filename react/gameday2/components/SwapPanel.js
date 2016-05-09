import React, { PropTypes } from 'react'
var classNames = require('classnames')

const SwapPanel = React.createClass({
  propTypes: {
    location: PropTypes.number.isRequired,
    layoutId: PropTypes.number.isRequired,
    enabled: PropTypes.bool.isRequired,
    close: PropTypes.func.isRequired
  },
  render: function() {
    var classes = classNames({
      'hidden': !this.props.enabled,
      'swap-panel': true
    })

    return (
      <div className={classes}>
        <button type="button" className="button-close btn btn-sm btn-default" onClick={this.props.close}>
          <span className="glyphicon glyphicon-remove"></span>
        </button>
      </div>
    )
  }
})

export default SwapPanel
