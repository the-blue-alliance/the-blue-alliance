import { NUM_VIEWS_FOR_LAYOUT } from '../constants/LayoutConstants'

// Convenience wrapper around NUM_VIEWS_FOR_LAYOUT that has bounds checking and
// a sensible default.
export function getNumViewsForLayout(layoutId) {
  if (layoutId >= 0 && layoutId < NUM_VIEWS_FOR_LAYOUT.length) {
    return NUM_VIEWS_FOR_LAYOUT[layoutId]
  }
  return 1
}
