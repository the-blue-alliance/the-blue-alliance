// How many layouts are defined
// Valid layout IDs are in the range [0, NUM_LAYOUTS - 1]
export const NUM_LAYOUTS = 9

// The maximum number of views any layout can support.
// Currently 9 for the nona-view
export const MAX_SUPPORTED_VIEWS = 9

// Maps a layout ID to the number of views that layout supports
// The layout ID is the index into this array
export const NUM_VIEWS_FOR_LAYOUT = [1, 2, 3, 4, 4, 5, 6, 8, 9]

// Maps a layout ID for the appropriate name for that layout
export const NAME_FOR_LAYOUT = [
  'Single View',
  'Split View',
  '"1+2" View',
  'Quad View',
  '"1+3" View',
  '"1+4" View',
  'Hex View',
  'Octo-View',
  'Nona-View',
]
