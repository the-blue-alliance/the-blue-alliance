"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Toolbar_1 = require("material-ui/Toolbar");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const FlatButton_1 = __importDefault(require("material-ui/FlatButton"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const IconButton_1 = __importDefault(require("material-ui/IconButton"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const muiThemeable_1 = __importDefault(
  require("material-ui/styles/muiThemeable")
);
const LayoutDrawer_1 = __importDefault(require("./LayoutDrawer"));
const layoutUtils_1 = require("../utils/layoutUtils");
const LampIcon_1 = __importDefault(require("./LampIcon"));
const AppBar = (props) => {
  const tbaBrandingButtonStyle = {
    padding: 0,
    marginLeft: 8,
    marginRight: 8,
    width: props.muiTheme.layout.appBarHeight,
    height: props.muiTheme.layout.appBarHeight,
  };
  const configureLayoutButtonStyle = {
    color: props.muiTheme.appBar.textColor,
  };
  const appBarStyle = {
    height: props.muiTheme.layout.appBarHeight,
    backgroundColor: props.muiTheme.palette.primary1Color,
    position: "relative",
    zIndex: props.muiTheme.zIndex.appBar,
    paddingRight: 0,
  };
  const appBarTitleStyle = {
    color: props.muiTheme.appBar.textColor,
    fontSize: "24px",
    overflow: "visible",
  };
  const appBarSubtitleStyle = {
    color: props.muiTheme.appBar.textColor,
    textDecoration: "none",
    fontSize: 12,
  };
  const vexProStyle = {
    color: props.muiTheme.appBar.textColor,
    textDecoration: "none",
    marginLeft: 32,
    marginRight: 64,
    fontSize: 12,
    display: "flex",
    alignItems: "center",
  };
  const tbaBrandingButton = jsx_runtime_1.jsx(
    IconButton_1.default,
    Object.assign(
      {
        style: tbaBrandingButtonStyle,
        tooltip: "Go to The Blue Alliance",
        tooltipPosition: "bottom-right",
        href: "https://www.thebluealliance.com",
      },
      {
        children: jsx_runtime_1.jsx(
          LampIcon_1.default,
          {
            width: props.muiTheme.layout.appBarHeight,
            height: props.muiTheme.layout.appBarHeight,
          },
          void 0
        ),
      }
    ),
    void 0
  );
  const configureLayoutButton = jsx_runtime_1.jsx(
    FlatButton_1.default,
    {
      label: "Configure Layout",
      labelPosition: "before",
      style: configureLayoutButtonStyle,
      icon: layoutUtils_1.getLayoutSvgIcon(props.layoutId, "#ffffff"),
      onClick: () => props.setLayoutDrawerVisibility(true),
    },
    void 0
  );
  return jsx_runtime_1.jsxs(
    "div",
    {
      children: [
        jsx_runtime_1.jsxs(
          Toolbar_1.Toolbar,
          Object.assign(
            { style: appBarStyle },
            {
              children: [
                jsx_runtime_1.jsxs(
                  Toolbar_1.ToolbarGroup,
                  Object.assign(
                    { firstChild: true },
                    {
                      children: [
                        tbaBrandingButton,
                        jsx_runtime_1.jsx(
                          Toolbar_1.ToolbarTitle,
                          { text: "GameDay", style: appBarTitleStyle },
                          void 0
                        ),
                        jsx_runtime_1.jsx(
                          "a",
                          Object.assign(
                            { style: appBarSubtitleStyle, href: "/" },
                            { children: "by The Blue Alliance" }
                          ),
                          void 0
                        ),
                        jsx_runtime_1.jsxs(
                          "a",
                          Object.assign(
                            {
                              style: vexProStyle,
                              href: "https://www.vexrobotics.com/vexpro/",
                            },
                            {
                              children: [
                                jsx_runtime_1.jsx(
                                  "span",
                                  Object.assign(
                                    { style: { marginRight: "4px" } },
                                    { children: "POWERED BY" }
                                  ),
                                  void 0
                                ),
                                jsx_runtime_1.jsx(
                                  "img",
                                  {
                                    src: "/images/vexpro_horiz.png",
                                    alt: "vexPRO",
                                    height: 16,
                                  },
                                  void 0
                                ),
                              ],
                            }
                          ),
                          void 0
                        ),
                        jsx_runtime_1.jsx(
                          "div",
                          {
                            className: "fb-like",
                            "data-href":
                              "https://www.facebook.com/thebluealliance/",
                            "data-layout": "button_count",
                            "data-action": "like",
                            "data-size": "small",
                            "data-show-faces": "false",
                            "data-share": "false",
                          },
                          void 0
                        ),
                      ],
                    }
                  ),
                  void 0
                ),
                jsx_runtime_1.jsx(
                  Toolbar_1.ToolbarGroup,
                  Object.assign(
                    { lastChild: true },
                    { children: configureLayoutButton }
                  ),
                  void 0
                ),
              ],
            }
          ),
          void 0
        ),
        jsx_runtime_1.jsx(
          LayoutDrawer_1.default,
          {
            setLayout: props.setLayout,
            toggleChatSidebarVisibility: props.toggleChatSidebarVisibility,
            toggleHashtagSidebarVisibility:
              props.toggleHashtagSidebarVisibility,
            selectedLayout: props.layoutId,
            layoutSet: props.layoutSet,
            chatSidebarVisible: props.chatSidebarVisible,
            hashtagSidebarVisible: props.hashtagSidebarVisible,
            layoutDrawerVisible: props.layoutDrawerVisible,
            setLayoutDrawerVisibility: props.setLayoutDrawerVisibility,
            hasWebcasts: props.webcasts.length > 0,
            resetWebcasts: props.resetWebcasts,
          },
          void 0
        ),
      ],
    },
    void 0
  );
};
exports.default = muiThemeable_1.default()(AppBar);
