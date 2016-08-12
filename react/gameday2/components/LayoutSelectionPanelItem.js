import React, { PropTypes } from 'react'
import classNames from 'classnames'
import { NUM_VIEWS_FOR_LAYOUT, NAME_FOR_LAYOUT } from '../constants/LayoutConstants'

export default React.createClass({
  propTypes: {
    layoutId: PropTypes.number.isRequired,
    setLayout: PropTypes.func.isRequired,
  },
  handleClick() {
    this.props.setLayout(this.props.layoutId)
  },
  render() {
    let videoViews = []
    const layoutId = this.props.layoutId
    for (let i = 0; i < NUM_VIEWS_FOR_LAYOUT[layoutId]; i++) {
      let className = `video-${i}`
      videoViews.push(
        <div className={className} key={className} />
      )
    }

    const containerClasses = classNames({
      'layout-preview': true,
      [`layout-${layoutId}`]: true,
    })

    return (
      <div className="col-md-4 layout-preview-container" onClick={this.handleClick} >
        <div className={containerClasses}>
          {videoViews}
        </div>
        <p>{NAME_FOR_LAYOUT[layoutId]}</p>
      </div>
    )
  },
})
