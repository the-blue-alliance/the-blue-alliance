import React, { PropTypes} from 'react'
import LayoutSelectionPanelItem from './LayoutSelectionPanelItem'
import { NUM_LAYOUTS } from '../constants/LayoutConstants'

const LayoutSelectionPanel = React.createClass({
  propTypes: {
    setLayout: PropTypes.func.isRequired
  },
  generateLayoutRows: function() {
    let rows = []
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
  render: function() {
    let rows = this.generateLayoutRows()
    return (
      <div className="layout-selection-panel" >
        <h1>Select a layout</h1>
        {rows}
      </div>
    )
  }
})

export default LayoutSelectionPanel
