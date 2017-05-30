import React, { PropTypes } from 'react'
import VideoCellContainer from '../containers/VideoCellContainer'
import { getNumViewsForLayout } from '../utils/layoutUtils'
import { webcastPropType } from '../utils/webcastUtils'

export default class VideoGrid extends React.Component {
  static propTypes = {
    domOrder: PropTypes.arrayOf(PropTypes.string).isRequired,
    positionMap: PropTypes.arrayOf(PropTypes.number).isRequired,
    webcastsById: PropTypes.objectOf(webcastPropType).isRequired,
    layoutId: PropTypes.number.isRequired,
  }

  renderLayout(webcastCount) {
    const videoGridStyle = {
      width: '100%',
      height: '100%',
    }

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
    const emptyCellPositions = []
    for (let i = 0; i < positionMap.length; i++) {
      if (positionMap[i] === -1 && i < webcastCount) {
        emptyCellPositions.push(i)
      }
    }

    // Render everything!
    const videoCells = []
    for (let i = 0; i < domOrder.length; i++) {
      let webcast = null
      let id = `video-${i}`
      let position = null
      let hasWebcast = true
      if (domOrder[i]) {
        // There's a webcast to display here!
        webcast = this.props.webcastsById[domOrder[i]]
        id = webcast.id
        position = idPositionMap[id]
      } else if (emptyCellPositions.length > 0) {
        position = emptyCellPositions.shift()
      } else {
        hasWebcast = false
      }
      if (hasWebcast) {
        videoCells.push(
          <VideoCellContainer
            position={position}
            key={id}
            webcast={webcast}
          />
        )
      } else {
        videoCells.push(
          <div key={i.toString()} />
        )
      }
    }

    return (
      <div style={videoGridStyle}>
        {videoCells}
      </div>
    )
  }

  render() {
    const selectedLayoutId = this.props.layoutId
    const numViews = getNumViewsForLayout(selectedLayoutId)
    return this.renderLayout(numViews, selectedLayoutId)
  }
}
