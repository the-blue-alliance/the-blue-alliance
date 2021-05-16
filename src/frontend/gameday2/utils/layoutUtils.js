"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
exports.default =
  exports.getLayoutSvgIcon =
  exports.getNumViewsForLayout =
    void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const SvgIcon_1 = __importDefault(require("material-ui/SvgIcon"));
const LayoutConstants_1 = require("../constants/LayoutConstants");
// Convenience wrapper around NUM_VIEWS_FOR_LAYOUT that has bounds checking and
// a sensible default.
function getNumViewsForLayout(layoutId) {
  if (
    layoutId >= 0 &&
    layoutId < LayoutConstants_1.NUM_VIEWS_FOR_LAYOUT.length
  ) {
    return LayoutConstants_1.NUM_VIEWS_FOR_LAYOUT[layoutId];
  }
  return 1;
}
exports.getNumViewsForLayout = getNumViewsForLayout;
exports.default = getNumViewsForLayout;
function getLayoutSvgIcon(layoutId, color = "#757575") {
  const pathData = LayoutConstants_1.LAYOUT_SVG_PATHS[layoutId];
  return jsx_runtime_1.jsx(
    SvgIcon_1.default,
    Object.assign(
      { color: color, viewBox: "0 0 23 15" },
      { children: jsx_runtime_1.jsx("path", { d: pathData }, void 0) }
    ),
    void 0
  );
}
exports.getLayoutSvgIcon = getLayoutSvgIcon;
