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

// Holds styling information about the various layouts

/* Layout 0: full screen single video

+------+------+
|             |
|      0      |
|             |
+------+------+

*/
const LAYOUT_0 = [
  {
    width: '100%',
    height: '100%',
    top: 0,
    left: 0,
    position: 'absolute',
  },
]

/* Layout 1: two videos side-by-side

+------+------+
|      |      |
|  0   |   1  |
|      |      |
+------+------+

*/
const LAYOUT_1 = [
  {
    width: '50%',
    height: '100%',
    top: 0,
    left: 0,
    position: 'absolute',
  }, {
    width: '50%',
    height: '100%',
    top: 0,
    left: '50%',
    position: 'absolute',
  },
]

/* Layout 2

+------+------+
|      |   1  |
|  0   |------|
|      |   2  |
+------+------+

*/
const LAYOUT_2 = [
  {
    width: '65%',
    height: '100%',
    top: 0,
    left: 0,
    position: 'absolute',
  }, {
    width: '35%',
    height: '50%',
    top: 0,
    left: '65%',
    position: 'absolute',
  }, {
    width: '35%',
    height: '50%',
    top: '50%',
    left: '65%',
    position: 'absolute',
  },
]

/* Layout 3

+------+------+
|   0  |   1  |
|------|------|
|   2  |   3  |
+------+------+

*/
const LAYOUT_3 = [
  {
    width: '50%',
    height: '50%',
    top: 0,
    left: 0,
    position: 'absolute',
  }, {
    width: '35%',
    height: '50%',
    top: 0,
    left: '50%',
    position: 'absolute',
  }, {
    width: '50%',
    height: '50%',
    top: '50%',
    left: 0,
    position: 'absolute',
  }, {
    width: '50%',
    height: '50%',
    top: '50%',
    left: '50%',
    position: 'absolute',
  },
]

/* Layout 4

+------+------+
|      |   1  |
|      |------|
|   0  |   2  |
|      |------|
|      |   3  |
+------+------+

*/
const LAYOUT_4 = [
  {
    width: '75%',
    height: '100%',
    top: 0,
    left: 0,
    position: 'absolute',
  }, {
    width: '25%',
    height: '33.33%',
    top: 0,
    left: '75%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '33.33%',
    top: '33.33%',
    left: '75%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '33.33%',
    top: '66.67%',
    left: '75%',
    position: 'absolute',
  },
]

/* Layout 5

+------+------+
|      |   1  |
|      |------|
|   0  |   2  |
|      |------|
|      |   3  |
|      |------|
|      |   4  |
+------+------+

*/
const LAYOUT_5 = [
  {
    width: '75%',
    height: '100%',
    top: 0,
    left: 0,
    position: 'absolute',
  }, {
    width: '25%',
    height: '25%',
    top: 0,
    left: '75%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '25%',
    top: '25%',
    left: '75%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '25%',
    top: '50%',
    left: '75%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '25%',
    top: '75%',
    left: '75%',
    position: 'absolute',
  },
]

/* Layout 6

+-----+-----+-----+
|  0  |  1  |  2  |
|-----|-----|-----|
|  3  |  4  |  5  |
+-----+-----+-----+

*/
const LAYOUT_6 = [
  {
    width: '33.33%',
    height: '50%',
    top: 0,
    left: 0,
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '50%',
    top: 0,
    left: '33.33%',
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '50%',
    top: 0,
    left: '66.67%',
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '50%',
    top: '50%',
    left: 0,
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '50%',
    top: '50%',
    left: '33.33%',
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '50%',
    top: '50%',
    left: '66.67%',
    position: 'absolute',
  },
]

/* Layout 7

+-----+-----+-----+-----+
|  0  |  1  |  2  |  3  |
|-----|-----|-----|-----|
|  4  |  5  |  6  |  7  |
+-----+-----+-----+-----+

*/
const LAYOUT_7 = [
  {
    width: '25%',
    height: '50%',
    top: 0,
    left: 0,
    position: 'absolute',
  }, {
    width: '25%',
    height: '50%',
    top: 0,
    left: '25%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '50%',
    top: 0,
    left: '50%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '50%',
    top: 0,
    left: '75%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '50%',
    top: '50%',
    left: 0,
    position: 'absolute',
  }, {
    width: '25%',
    height: '50%',
    top: '50%',
    left: '25%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '50%',
    top: '50%',
    left: '50%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '50%',
    top: '50%',
    left: '75%',
    position: 'absolute',
  },
]

/* Layout 8

+-----+-----+-----+
|  0  |  1  |  2  |
|-----|-----|-----|
|  3  |  4  |  5  |
|-----|-----|-----|
|  6  |  7  |  8  |
+-----+-----+-----+

*/
const LAYOUT_8 = [
  {
    width: '33.33%',
    height: '33.33%',
    top: 0,
    left: 0,
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '33.33%',
    top: 0,
    left: '33.33%',
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '33.33%',
    top: 0,
    left: '66.67%',
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '33.33%',
    top: '33.33',
    left: 0,
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '33.33%',
    top: '33.33%',
    left: '33.33%',
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '33.33%',
    top: '33.33%',
    left: '66.67%',
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '33.33%',
    top: '66.67%',
    left: 0,
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '33.33%',
    top: '66.67%',
    left: '33.33%',
    position: 'absolute',
  }, {
    width: '33.33%',
    height: '33.33%',
    top: '66.67%',
    left: '66.67%',
    position: 'absolute',
  },
]

export const LAYOUT_STYLES = [
  LAYOUT_0,
  LAYOUT_1,
  LAYOUT_2,
  LAYOUT_3,
  LAYOUT_4,
  LAYOUT_5,
  LAYOUT_6,
  LAYOUT_7,
  LAYOUT_8,
]
