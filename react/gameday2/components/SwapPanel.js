import React, { PropTypes } from 'react'
import { NUM_VIEWS_FOR_LAYOUT } from '../constants/LayoutConstants'

const classNames = require('classnames')

const SwapPanel = React.createClass({
  propTypes: {
    location: PropTypes.number.isRequired,
    layoutId: PropTypes.number.isRequired,
    enabled: PropTypes.bool.isRequired,
    close: PropTypes.func.isRequired,
    swapToLocation: PropTypes.func.isRequired,
  },
  swapLocationSelected(location) {
    this.props.swapToLocation(location)
  },
  render() {
    let videoViews = []
    const layoutId = this.props.layoutId
    for (let i = 0; i < NUM_VIEWS_FOR_LAYOUT[layoutId]; i++) {
      let className = classNames({
        [`video-${i}`]: true,
        'current-location': i === this.props.location,
      })
      /* eslint-disable react/jsx-no-bind */
      // Disabling this is OK because this component doesn't re-render
      // frequently, so there is no real performance hit caused by creating a
      // brand new function on every single render.
      videoViews.push(
        <div className={className} key={className} onClick={this.swapLocationSelected.bind(this, i)} />
      )
      /* eslint-enable react/jsx-no-bind */
    }

    const containerClasses = classNames({
      'layout-preview': true,
      [`layout-${layoutId}`]: true,
    })

    const classes = classNames({
      hidden: !this.props.enabled,
      'swap-panel': true,
    })

    return (
      <div className={classes}>
        <button type="button" className="button-close btn btn-sm btn-default" onClick={this.props.close}>
          <span className="glyphicon glyphicon-remove" />
        </button>
        <div className="layout-preview-container">
          <div className={containerClasses}>
            {videoViews}
          </div>
        </div>
      </div>
    )
  },
})

export default SwapPanel
