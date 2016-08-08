import React, { PropTypes } from 'react'
import LayoutSelectionPanelItem from './LayoutSelectionPanelItem'
import { NUM_LAYOUTS } from '../constants/LayoutConstants'

export default React.createClass({
  propTypes: {
    setLayout: PropTypes.func.isRequired,
  },
  generateLayoutRows() {
    const rows = []
    let currentRow = []
    let rowNum = 0
    for (let i = 0; i < NUM_LAYOUTS; i++) {
      let layoutKey = 'layout-' + i
      currentRow.push(
        <LayoutSelectionPanelItem layoutId={i} key={layoutKey} setLayout={this.props.setLayout} />
      )
      if (currentRow.length >= 3) {
        rows.push(
          <div className="row" key={rowNum} >
            {currentRow}
          </div>)
        currentRow = []
        rowNum++
      }
    }
    return rows
  },
  render() {
    let rows = this.generateLayoutRows()
    return (
      <div className="layout-selection-panel" >
        <h1>Select a layout</h1>
        {rows}
      </div>
    )
  },
})
