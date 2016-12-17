/* eslint-disable import/prefer-default-export */
import React from 'react'
import SvgIcon from 'material-ui/SvgIcon'
import { NUM_VIEWS_FOR_LAYOUT, LAYOUT_SVG_PATHS } from '../constants/LayoutConstants'

// Convenience wrapper around NUM_VIEWS_FOR_LAYOUT that has bounds checking and
// a sensible default.
export function getNumViewsForLayout(layoutId) {
  if (layoutId >= 0 && layoutId < NUM_VIEWS_FOR_LAYOUT.length) {
    return NUM_VIEWS_FOR_LAYOUT[layoutId]
  }
  return 1
}

export function getLayoutSvgIcon(layoutId, color = '#757575') {
  const pathData = LAYOUT_SVG_PATHS[layoutId]
  return (
    <SvgIcon color={color} viewBox="0 0 23 15">
      <path d={pathData} />
    </SvgIcon>
  )
}

export { getNumViewsForLayout as default }
