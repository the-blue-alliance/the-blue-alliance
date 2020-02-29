// How many layouts are defined
// Valid layout IDs are in the range [0, NUM_LAYOUTS - 1]
export const NUM_LAYOUTS = 12

// The maximum number of views any layout can support.
// Currently 9 for the nona-view
export const MAX_SUPPORTED_VIEWS = 9

// Maps a layout ID to the number of views that layout supports
// The layout ID is the index into this array
export const NUM_VIEWS_FOR_LAYOUT = [1, 2, 3, 4, 4, 5, 6, 8, 9, 2, 7, 8]

// Defines the order layouts are shown in the layout selection list
// Each element is the number of the layout that should be shown at that index
export const LAYOUT_DISPLAY_ORDER = [0, 1, 9, 2, 3, 4, 5, 6, 10, 7, 11, 8]

// Maps a layout ID for the appropriate name for that layout
export const NAME_FOR_LAYOUT = [
  'Single View',
  'Vertical Split View',
  '"1+2" View',
  'Quad View',
  '"1+3" View',
  '"1+4" View',
  'Hex View',
  'Octo-View',
  'Nona-View',
  'Horizontal Split View',
  '"1+6" View',
  'Octo-View (Vertical)',
]

// Holds SVG path data that can be used to render icons for each layout
// See http://codepen.io/nwalters512/pen/XNoGwm
export const LAYOUT_SVG_PATHS = [
  'M0 0h23v15h-23v-15z',
  'M0 0h11v15h-11v-15zM12 0h11v15h-11v-15z',
  'M0 0h14v15h-14v-15zM15 0h8v7h-8v-7zM15 8h8v7h-8v-7z',
  'M0 0h11v7h-11v-7z M0 8h11v7h-11v-7z M12 0h11v7h-11v-7z M12 8h11v7h-11v-7z',
  'M0 0h14v15h-14v-15z M15 0h8v4.333h-8v-4.33z M15 5.33h8v4.333h-8v-4.33z M15 10.67h8v4.333h-8v-4.33z',
  'M0 0h15v15h-15v-15z M16 0h7v3h-7v-3z M16 4h7v3h-7v3z M16 8h7v3h-7v-3z M16 12h7v3h-7v-3z',
  'M0 0h7v7h-7v-7z M8 0h7v7h-7v-7z M16 0h7v7h-7v-7z M8 8h7v7h-7v-7z M16 8h7v7h-7v-7z M0 8h7v7h-7v-7z',
  'M0 0h5v7h-5v-7z M6 0h5v7h-5v-7z M12 0h5v7h-5v-7z M18 0h5v7h-5v-7z M0 8h5v7h-5v-7z M6 8h5v7h-5v-7z M12 8h5v7h-5v-7z M18 8h5v7h-5v-7z',
  'M0 0h7v4.33h-7v-4.33z M8 0h7v4.33h-7v-4.33z M16 0h7v4.33h-7v-4.33z M0 5.33h7v4.33h-7v-4.33z M8 5.33h7v4.33h-7v-4.33z M16 5.33h7v4.33h-7v-4.33z M0 10.67h7v4.33h-7v-4.33z M8 10.67h7v4.33h-7v-4.33z M16 10.67h7v4.33h-7v-4.33z',
  'M0 0h23v7h-23v-7z M0 8h23v7h-23v-7z',
  'M0,0h17v9.8H0V0z M17.7,0H23v4.6h-5.3v4.6V0z M17.7,5.2H23v4.6h-5.3v4.6V5.2z M5.9,10.3h5.3V15H5.9v4.7V10.3z M0,10.3h5.3V15H0v4.7V10.3z M11.8,10.4H17V15h-5.3v4.6C11.8,19.7,11.8,10.4,11.8,10.4z M17.7,10.4H23V15h-5.3v4.6V10.4z',
  'M0 0h11v3h-11v-3z M0 4h11v3h-11v-3z M0 8h11v3h-11v-3z M0 12h11v3h-11v-3z M12 0h11v3h-11v-3z M12 4h11v3h-11v-3z M12 8h11v3h-11v-3z M12 12h11v3h-11v-3z',
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
    width: '50%',
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
    top: '33.33%',
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


/* Layout 9

 +-------------+
 |      0      |
 |-------------|
 |      1      |
 +-------------+

 */
const LAYOUT_9 = [
  {
    width: '100%',
    height: '50%',
    top: 0,
    left: 0,
    position: 'absolute',
  }, {
    width: '100%',
    height: '50%',
    top: '50%',
    left: 0,
    position: 'absolute',
  },
]


/* Layout 10

+-----------+------+------+
|                  |   1  |
|         0        |------|
|                  |   2  |
|------------------|------|
|  6  |  5   |  4  |   3  |
+-----+------+-----+------+

 */
const LAYOUT_10 = [
  {
    width: '75%',
    height: '66.67%',
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
  }, {
    width: '25%',
    height: '33.33%',
    top: '66.67%',
    left: '50%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '33.33%',
    top: '66.67%',
    left: '25%',
    position: 'absolute',
  }, {
    width: '25%',
    height: '33.33%',
    top: '66.67%',
    left: 0,
    position: 'absolute',
  },
]


/* Layout 11
+------+------+
|   0  |   1  |
|------|------|
|   2  |   3  |
|------|------|
|   4  |   5  |
|------|------|
|   6  |   7  |
+------+------+


*/
const LAYOUT_11 = [
  {
    width: '50%',
    height: '25%',
    top: 0,
    left: 0,
    position: 'absolute',
  }, {
    width: '50%',
    height: '25%',
    top: '25%',
    left: 0,
    position: 'absolute',
  }, {
    width: '50%',
    height: '25%',
    top: '50%',
    left: 0,
    position: 'absolute',
  }, {
    width: '50%',
    height: '25%',
    top: '75%',
    left: 0,
    position: 'absolute',
  }, {
    width: '50%',
    height: '25%',
    top: 0,
    left: '50%',
    position: 'absolute',
  }, {
    width: '50%',
    height: '25%',
    top: '25%',
    left: '50%',
    position: 'absolute',
  }, {
    width: '50%',
    height: '25%',
    top: '50%',
    left: '50%',
    position: 'absolute',
  }, {
    width: '50%',
    height: '25%',
    top: '75%',
    left: '50%',
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
  LAYOUT_9,
  LAYOUT_10,
  LAYOUT_11,
]
