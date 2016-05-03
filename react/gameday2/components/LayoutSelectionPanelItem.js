import React, { PropTypes} from 'react'
import { NUM_VIEWS_FOR_LAYOUT, NAME_FOR_LAYOUT } from '../constants/LayoutConstants'
let classNames = require('classnames')

const LayoutSelectionPanelItem = React.createClass({
  propTypes: {
    layoutId: PropTypes.number.isRequired,
    setLayout: PropTypes.func.isRequired
  },
  handleClick: function() {
    this.props.setLayout(this.props.layoutId)
  },
  render: function() {
    let videoViews = []
    let layoutId = this.props.layoutId
    for(let i = 0; i < NUM_VIEWS_FOR_LAYOUT[layoutId]; i++) {
      let className = ("video-" + i)
      videoViews.push(
        <div className={className} key={className} />
      )
    }
    let containerClasses = 'layout-preview layout-' + layoutId
    return (
      <div className="col-md-4 layout-preview-container" onClick={this.handleClick} >
        <div className={containerClasses}>
          {videoViews}
        </div>
        <p>{NAME_FOR_LAYOUT[layoutId]}</p>
      </div>
    )
  }
})

export default LayoutSelectionPanelItem
