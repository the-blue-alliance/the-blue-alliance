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
const muiThemeable_1 = __importDefault(
  require("material-ui/styles/muiThemeable")
);
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const RaisedButton_1 = __importDefault(require("material-ui/RaisedButton"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Drawer_1 = __importDefault(require("material-ui/Drawer"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Divider_1 = __importDefault(require("material-ui/Divider"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const List_1 = require("material-ui/List");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Subheader_1 = __importDefault(require("material-ui/Subheader"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Toggle_1 = __importDefault(require("material-ui/Toggle"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const colors_1 = require("material-ui/styles/colors");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const check_1 = __importDefault(
  require("material-ui/svg-icons/navigation/check")
);
const layoutUtils_1 = require("../utils/layoutUtils");
const LayoutConstants_1 = require("../constants/LayoutConstants");
class LayoutDrawer extends react_1.default.Component {
  handleResetWebcasts() {
    this.props.resetWebcasts();
  }
  render() {
    // If there aren't any webcasts, display a message instead
    // of unselectable checkboxes
    const layouts = [];
    if (this.props.hasWebcasts) {
      for (let i = 0; i < LayoutConstants_1.NUM_LAYOUTS; i++) {
        const layoutNum = LayoutConstants_1.LAYOUT_DISPLAY_ORDER[i];
        const showCheck =
          layoutNum === this.props.selectedLayout && this.props.layoutSet;
        const icon = showCheck
          ? jsx_runtime_1.jsx(check_1.default, {}, void 0)
          : null;
        layouts.push(
          jsx_runtime_1.jsx(
            List_1.ListItem,
            {
              primaryText: LayoutConstants_1.NAME_FOR_LAYOUT[layoutNum],
              insetChildren: true,
              onClick: () => this.props.setLayout(layoutNum),
              rightIcon: icon,
              leftIcon: layoutUtils_1.getLayoutSvgIcon(layoutNum),
            },
            i.toString()
          )
        );
      }
    } else {
      layouts.push(
        jsx_runtime_1.jsx(
          List_1.ListItem,
          {
            primaryText:
              "There aren't any webcasts available right now. Check back later!",
            disabled: true,
          },
          "empty"
        )
      );
    }
    const chatToggle = jsx_runtime_1.jsx(
      Toggle_1.default,
      {
        onToggle: () => this.props.toggleChatSidebarVisibility(),
        toggled: this.props.chatSidebarVisible,
      },
      void 0
    );
    const hashtagToggle = jsx_runtime_1.jsx(
      Toggle_1.default,
      {
        onToggle: () => this.props.toggleHashtagSidebarVisibility(),
        toggled: this.props.hashtagSidebarVisible,
      },
      void 0
    );
    const primaryColor = this.props.muiTheme.palette.primary1Color;
    return jsx_runtime_1.jsx(
      Drawer_1.default,
      Object.assign(
        {
          docked: false,
          open: this.props.layoutDrawerVisible,
          onRequestChange: (open) => this.props.setLayoutDrawerVisibility(open),
          openSecondary: true,
          width: 300,
        },
        {
          children: jsx_runtime_1.jsxs(
            "div",
            {
              children: [
                jsx_runtime_1.jsxs(
                  List_1.List,
                  {
                    children: [
                      jsx_runtime_1.jsx(
                        Subheader_1.default,
                        Object.assign(
                          { style: { color: primaryColor } },
                          { children: "Select video grid layout" }
                        ),
                        void 0
                      ),
                      layouts,
                    ],
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(Divider_1.default, {}, void 0),
                jsx_runtime_1.jsxs(
                  List_1.List,
                  {
                    children: [
                      jsx_runtime_1.jsx(
                        Subheader_1.default,
                        Object.assign(
                          { style: { color: primaryColor } },
                          { children: "Enable/disable sidebars" }
                        ),
                        void 0
                      ),
                      jsx_runtime_1.jsx(
                        List_1.ListItem,
                        {
                          primaryText: "Social Sidebar",
                          rightToggle: hashtagToggle,
                        },
                        void 0
                      ),
                      jsx_runtime_1.jsx(
                        List_1.ListItem,
                        {
                          primaryText: "Chat Sidebar",
                          rightToggle: chatToggle,
                        },
                        void 0
                      ),
                    ],
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(Divider_1.default, {}, void 0),
                jsx_runtime_1.jsx(
                  "div",
                  Object.assign(
                    { style: { padding: 8 } },
                    {
                      children: jsx_runtime_1.jsx(
                        RaisedButton_1.default,
                        {
                          label: "Reset Webcasts",
                          backgroundColor: colors_1.red500,
                          labelColor: colors_1.fullWhite,
                          fullWidth: true,
                          onClick: () => this.handleResetWebcasts(),
                        },
                        void 0
                      ),
                    }
                  ),
                  void 0
                ),
              ],
            },
            void 0
          ),
        }
      ),
      void 0
    );
  }
}
exports.default = muiThemeable_1.default()(LayoutDrawer);
