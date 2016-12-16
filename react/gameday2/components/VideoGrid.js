import React, { PropTypes } from 'react'
import classNames from 'classnames'
import VideoCell from './VideoCell'
import { getNumViewsForLayout } from '../utils/layoutUtils'

export default React.createClass({
  propTypes: {
    displayedWebcasts: PropTypes.array.isRequired,
    domOrder: PropTypes.array.isRequired,
    positionMap: PropTypes.array.isRequired,
    webcasts: PropTypes.array.isRequired,
    webcastsById: PropTypes.object.isRequired,
    layoutId: PropTypes.number.isRequired,
    addWebcastAtLocation: PropTypes.func.isRequired,
  },
  renderLayout(webcastCount, layoutNumber) {
    const classes = classNames({
      [`layout-${layoutNumber}`]: true,
      'video-grid': true,
    })

    const {
      domOrder,
      positionMap,
    } = this.props

    // Set up reverse map between webcast ID and position
    const idPositionMap = {}
    for (let i = 0; i < positionMap.length; i++) {
      const webcastId = domOrder[positionMap[i]]
      if (webcastId != null) {
        idPositionMap[webcastId] = i
      }
    }

    // Compute which cells don't a webcast in them
    const emptyCellLocations = []
    for (let i = 0; i < positionMap.length; i++) {
      if (positionMap[i] === -1 && i < webcastCount) {
        emptyCellLocations.push(i)
      }
    }

    // Render everything!
    const videoCells = []
    for (let i = 0; i < domOrder.length; i++) {
      let webcast = null
      let id = `video-${i}`
      let location = null
      let hasWebcast = true
      if (domOrder[i]) {
        // There's a webcast to display here!
        webcast = this.props.webcastsById[domOrder[i]]
        id = webcast.id
        location = idPositionMap[id]
      } else if (emptyCellLocations.length > 0) {
        location = emptyCellLocations.shift()
      } else {
        hasWebcast = false
      }
      if (hasWebcast) {
        videoCells.push(
          <VideoCell
            location={location}
            key={id}
            webcast={webcast}
            webcasts={this.props.webcasts}
            webcastsById={this.props.webcastsById}
            displayedWebcasts={this.props.displayedWebcasts}
            addWebcastAtLocation={this.props.addWebcastAtLocation}
          />
        )
      } else {
        videoCells.push(
          <div />
        )
      }
    }

    return (
      <div className={classes}>
        {videoCells}
      </div>
    )
  },
  render() {
    const selectedLayoutId = this.props.layoutId
    const numViews = getNumViewsForLayout(selectedLayoutId)
    return this.renderLayout(numViews, selectedLayoutId)
  },
})
