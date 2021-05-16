"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const List_1 = require("material-ui/List");
class WebcastSelectionDialogItem extends react_1.default.Component {
  handleClick() {
    this.props.webcastSelected(this.props.webcast.id);
  }
  render() {
    return jsx_runtime_1.jsx(
      List_1.ListItem,
      {
        primaryText: this.props.webcast.name,
        secondaryText: this.props.secondaryText,
        onClick: () => this.handleClick(),
        rightIcon: this.props.rightIcon,
      },
      void 0
    );
  }
}
exports.default = WebcastSelectionDialogItem;
