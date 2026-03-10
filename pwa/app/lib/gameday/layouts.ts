/**
 * Layout configuration for the video grid
 */
interface LayoutConfig {
  /** Human-readable name */
  name: string;
  /** Number of views this layout supports */
  numViews: number;
  /** CSS grid template for this layout */
  gridTemplate: string;
  /** Grid areas for each cell position */
  gridAreas: string[];
  /** SVG path data for the layout icon */
  svgPath: string;
}

/**
 * Maximum number of views any layout can support
 */
export const MAX_VIEWS = 9;

/**
 * Layout definitions for the video grid
 * Each layout defines a CSS grid template and the areas for each cell
 */
const LAYOUTS: LayoutConfig[] = [
  // Layout 0: Single View
  {
    name: 'Single View',
    numViews: 1,
    gridTemplate: '"a" 1fr / 1fr',
    gridAreas: ['a'],
    svgPath: 'M0 0h23v15h-23v-15z',
  },
  // Layout 1: Vertical Split (side-by-side)
  {
    name: 'Vertical Split',
    numViews: 2,
    gridTemplate: '"a b" 1fr / 1fr 1fr',
    gridAreas: ['a', 'b'],
    svgPath: 'M0 0h11v15h-11v-15zM12 0h11v15h-11v-15z',
  },
  // Layout 2: 1+2 View
  {
    name: '"1+2" View',
    numViews: 3,
    gridTemplate: '"a b" 1fr "a c" 1fr / 2fr 1fr',
    gridAreas: ['a', 'b', 'c'],
    svgPath: 'M0 0h14v15h-14v-15zM15 0h8v7h-8v-7zM15 8h8v7h-8v-7z',
  },
  // Layout 3: Quad View
  {
    name: 'Quad View',
    numViews: 4,
    gridTemplate: '"a b" 1fr "c d" 1fr / 1fr 1fr',
    gridAreas: ['a', 'b', 'c', 'd'],
    svgPath:
      'M0 0h11v7h-11v-7z M0 8h11v7h-11v-7z M12 0h11v7h-11v-7z M12 8h11v7h-11v-7z',
  },
  // Layout 4: 1+3 View
  {
    name: '"1+3" View',
    numViews: 4,
    gridTemplate: '"a b" 1fr "a c" 1fr "a d" 1fr / 3fr 1fr',
    gridAreas: ['a', 'b', 'c', 'd'],
    svgPath:
      'M0 0h14v15h-14v-15z M15 0h8v4.333h-8v-4.33z M15 5.33h8v4.333h-8v-4.33z M15 10.67h8v4.333h-8v-4.33z',
  },
  // Layout 5: 1+4 View
  {
    name: '"1+4" View',
    numViews: 5,
    gridTemplate: '"a b" 1fr "a c" 1fr "a d" 1fr "a e" 1fr / 3fr 1fr',
    gridAreas: ['a', 'b', 'c', 'd', 'e'],
    svgPath:
      'M0 0h15v15h-15v-15z M16 0h7v3h-7v-3z M16 4h7v3h-7v3z M16 8h7v3h-7v-3z M16 12h7v3h-7v-3z',
  },
  // Layout 6: Hex View (3x2)
  {
    name: 'Hex View',
    numViews: 6,
    gridTemplate: '"a b c" 1fr "d e f" 1fr / 1fr 1fr 1fr',
    gridAreas: ['a', 'b', 'c', 'd', 'e', 'f'],
    svgPath:
      'M0 0h7v7h-7v-7z M8 0h7v7h-7v-7z M16 0h7v7h-7v-7z M8 8h7v7h-7v-7z M16 8h7v7h-7v-7z M0 8h7v7h-7v-7z',
  },
  // Layout 7: Octo-View (4x2)
  {
    name: 'Octo-View',
    numViews: 8,
    gridTemplate: '"a b c d" 1fr "e f g h" 1fr / 1fr 1fr 1fr 1fr',
    gridAreas: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
    svgPath:
      'M0 0h5v7h-5v-7z M6 0h5v7h-5v-7z M12 0h5v7h-5v-7z M18 0h5v7h-5v-7z M0 8h5v7h-5v-7z M6 8h5v7h-5v-7z M12 8h5v7h-5v-7z M18 8h5v7h-5v-7z',
  },
  // Layout 8: Nona-View (3x3)
  {
    name: 'Nona-View',
    numViews: 9,
    gridTemplate: '"a b c" 1fr "d e f" 1fr "g h i" 1fr / 1fr 1fr 1fr',
    gridAreas: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'],
    svgPath:
      'M0 0h7v4.33h-7v-4.33z M8 0h7v4.33h-7v-4.33z M16 0h7v4.33h-7v-4.33z M0 5.33h7v4.33h-7v-4.33z M8 5.33h7v4.33h-7v-4.33z M16 5.33h7v4.33h-7v-4.33z M0 10.67h7v4.33h-7v-4.33z M8 10.67h7v4.33h-7v-4.33z M16 10.67h7v4.33h-7v-4.33z',
  },
  // Layout 9: Horizontal Split (stacked)
  {
    name: 'Horizontal Split',
    numViews: 2,
    gridTemplate: '"a" 1fr "b" 1fr / 1fr',
    gridAreas: ['a', 'b'],
    svgPath: 'M0 0h23v7h-23v-7z M0 8h23v7h-23v-7z',
  },
  // Layout 10: 1+6 View
  {
    name: '"1+6" View',
    numViews: 7,
    gridTemplate: '"a a a b" 1fr "a a a c" 1fr "g f e d" 1fr / 1fr 1fr 1fr 1fr',
    gridAreas: ['a', 'b', 'c', 'd', 'e', 'f', 'g'],
    svgPath:
      'M0,0h17v9.8H0V0z M17.7,0H23v4.6h-5.3v4.6V0z M17.7,5.2H23v4.6h-5.3v4.6V5.2z M5.9,10.3h5.3V15H5.9v4.7V10.3z M0,10.3h5.3V15H0v4.7V10.3z M11.8,10.4H17V15h-5.3v4.6C11.8,19.7,11.8,10.4,11.8,10.4z M17.7,10.4H23V15h-5.3v4.6V10.4z',
  },
  // Layout 11: Octo-View Vertical (2x4)
  {
    name: 'Octo-View (Vertical)',
    numViews: 8,
    gridTemplate: '"a e" 1fr "b f" 1fr "c g" 1fr "d h" 1fr / 1fr 1fr',
    gridAreas: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
    svgPath:
      'M0 0h11v3h-11v-3z M0 4h11v3h-11v-3z M0 8h11v3h-11v-3z M0 12h11v3h-11v-3z M12 0h11v3h-11v-3z M12 4h11v3h-11v-3z M12 8h11v3h-11v-3z M12 12h11v3h-11v-3z',
  },
];

/**
 * Named indices into the LAYOUTS array
 */
export const Layout = {
  SINGLE_VIEW: 0,
  VERTICAL_SPLIT: 1,
  ONE_PLUS_TWO: 2,
  QUAD_VIEW: 3,
  ONE_PLUS_THREE: 4,
  ONE_PLUS_FOUR: 5,
  HEX_VIEW: 6,
  OCTO_VIEW: 7,
  NONA_VIEW: 8,
  HORIZONTAL_SPLIT: 9,
  ONE_PLUS_SIX: 10,
  OCTO_VIEW_VERTICAL: 11,
} as const;

/**
 * Order in which layouts should be displayed in the selection UI
 */
export const LAYOUT_DISPLAY_ORDER = [
  Layout.SINGLE_VIEW,
  Layout.VERTICAL_SPLIT,
  Layout.HORIZONTAL_SPLIT,
  Layout.ONE_PLUS_TWO,
  Layout.QUAD_VIEW,
  Layout.ONE_PLUS_THREE,
  Layout.ONE_PLUS_FOUR,
  Layout.HEX_VIEW,
  Layout.ONE_PLUS_SIX,
  Layout.OCTO_VIEW,
  Layout.OCTO_VIEW_VERTICAL,
  Layout.NONA_VIEW,
];

/**
 * Get a layout by its index
 */
export function getLayoutById(id: number | null): LayoutConfig | undefined {
  if (id === null) return undefined;
  return LAYOUTS[id];
}

/**
 * Get the number of views for a layout
 */
export function getNumViewsForLayout(layoutId: number): number {
  const layout = getLayoutById(layoutId);
  return layout?.numViews ?? 1;
}

/**
 * Pick the best layout index to display a given number of webcasts
 */
export function getBestLayoutForCount(count: number): number {
  if (count <= 1) return Layout.SINGLE_VIEW;
  if (count <= 2) return Layout.VERTICAL_SPLIT;
  if (count <= 3) return Layout.ONE_PLUS_TWO;
  if (count <= 4) return Layout.QUAD_VIEW;
  if (count <= 5) return Layout.ONE_PLUS_FOUR;
  if (count <= 6) return Layout.HEX_VIEW;
  if (count <= 8) return Layout.OCTO_VIEW;
  return Layout.NONA_VIEW;
}
