import React, { PropTypes } from 'react'
import LayoutSelectionPanelItem from './LayoutSelectionPanelItem'
import { NUM_LAYOUTS } from '../constants/LayoutConstants'

export default class LayoutSelectionPanel extends React.Component {
  static propTypes = {
    setLayout: PropTypes.func.isRequired,
  }

  generateLayoutRows() {
    const rows = []
    let currentRow = []
    let rowNum = 0
    for (let i = 0; i < NUM_LAYOUTS; i++) {
      const layoutKey = `layout-${i}`
      currentRow.push(
        <LayoutSelectionPanelItem layoutId={i} key={layoutKey} setLayout={(layoutId) => this.props.setLayout(layoutId)} />
      )
      if (currentRow.length >= 3) {
        rows.push(
          <div className="row" key={rowNum} >
            {currentRow}
          </div>)
        currentRow = []
        /* eslint-disable no-plusplus */
        rowNum++
      }
    }
    return rows
  }

  render() {
    const rows = this.generateLayoutRows()
    return (
      <div className="layout-selection-panel" >
        <h1>Select a layout</h1>
        {rows}
      </div>
    )
  }
}
