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
const Dialog_1 = __importDefault(require("material-ui/Dialog"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const colors_1 = require("material-ui/styles/colors");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Divider_1 = __importDefault(require("material-ui/Divider"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const FlatButton_1 = __importDefault(require("material-ui/FlatButton"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const List_1 = require("material-ui/List");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Subheader_1 = __importDefault(require("material-ui/Subheader"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const grade_1 = __importDefault(require("material-ui/svg-icons/action/grade"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const help_1 = __importDefault(require("material-ui/svg-icons/action/help"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const videocam_1 = __importDefault(
  require("material-ui/svg-icons/av/videocam")
);
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const videocam_off_1 = __importDefault(
  require("material-ui/svg-icons/av/videocam-off")
);
const WebcastSelectionDialogItem_1 = __importDefault(
  require("./WebcastSelectionDialogItem")
);
class WebcastSelectionDialog extends react_1.default.Component {
  onRequestClose() {
    if (this.props.onRequestClose) {
      this.props.onRequestClose();
    }
  }
  render() {
    const subheaderStyle = {
      color: colors_1.indigo500,
    };
    // Construct list of webcasts
    const bluezoneWebcastItems = [];
    const specialWebcastItems = [];
    const webcastItems = [];
    const offlineSpecialWebcastItems = [];
    const offlineWebcastItems = [];
    // Don't let the user choose a webcast that is already displayed elsewhere
    const availableWebcasts = this.props.webcasts.filter(
      (webcastId) => this.props.displayedWebcasts.indexOf(webcastId) === -1
    );
    availableWebcasts.forEach((webcastId) => {
      const webcast = this.props.webcastsById[webcastId];
      let rightIcon = jsx_runtime_1.jsx(help_1.default, {}, void 0);
      let secondaryText = null;
      if (webcast.status === "online") {
        rightIcon = jsx_runtime_1.jsxs(
          "div",
          Object.assign(
            {
              style: {
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                width: 96,
              },
            },
            {
              children: [
                webcast.viewerCount &&
                  jsx_runtime_1.jsxs(
                    "small",
                    Object.assign(
                      {
                        style: {
                          textAlign: "center",
                          marginRight: 8,
                        },
                      },
                      {
                        children: [
                          webcast.viewerCount.toLocaleString(),
                          jsx_runtime_1.jsx("br", {}, void 0),
                          "Viewers",
                        ],
                      }
                    ),
                    void 0
                  ),
                jsx_runtime_1.jsx(
                  videocam_1.default,
                  { color: colors_1.green500 },
                  void 0
                ),
              ],
            }
          ),
          void 0
        );
        if (webcast.streamTitle) {
          secondaryText = webcast.streamTitle;
        }
      } else if (webcast.status === "offline") {
        rightIcon = jsx_runtime_1.jsx(videocam_off_1.default, {}, void 0);
      }
      if (this.props.specialWebcastIds.has(webcast.id)) {
        const item = jsx_runtime_1.jsx(
          WebcastSelectionDialogItem_1.default,
          {
            webcast: webcast,
            webcastSelected: this.props.onWebcastSelected,
            secondaryText: secondaryText,
            rightIcon: rightIcon,
          },
          webcast.id
        );
        if (webcast.status === "offline") {
          offlineSpecialWebcastItems.push(item);
        } else {
          specialWebcastItems.push(item);
        }
      } else if (webcast.id.startsWith("bluezone")) {
        bluezoneWebcastItems.push(
          jsx_runtime_1.jsx(
            WebcastSelectionDialogItem_1.default,
            {
              webcast: webcast,
              webcastSelected: this.props.onWebcastSelected,
              secondaryText: "The best matches from across FRC",
              rightIcon: jsx_runtime_1.jsx(
                grade_1.default,
                { color: colors_1.indigo500 },
                void 0
              ),
            },
            webcast.id
          )
        );
      } else {
        const item = jsx_runtime_1.jsx(
          WebcastSelectionDialogItem_1.default,
          {
            webcast: webcast,
            webcastSelected: this.props.onWebcastSelected,
            secondaryText: secondaryText,
            rightIcon: rightIcon,
          },
          webcast.id
        );
        if (webcast.status === "offline") {
          offlineWebcastItems.push(item);
        } else {
          webcastItems.push(item);
        }
      }
    });
    let allWebcastItems = [];
    if (specialWebcastItems.length !== 0 || bluezoneWebcastItems.length !== 0) {
      allWebcastItems.push(
        jsx_runtime_1.jsx(
          Subheader_1.default,
          Object.assign(
            { style: subheaderStyle },
            { children: "Special Webcasts" }
          ),
          "specialWebcastsHeader"
        )
      );
      allWebcastItems = allWebcastItems.concat(bluezoneWebcastItems);
      allWebcastItems = allWebcastItems.concat(specialWebcastItems);
    }
    if (webcastItems.length !== 0) {
      if (specialWebcastItems.length !== 0) {
        allWebcastItems.push(
          jsx_runtime_1.jsx(Divider_1.default, {}, "eventWebcastsDivider")
        );
      }
      allWebcastItems.push(
        jsx_runtime_1.jsx(
          Subheader_1.default,
          Object.assign(
            { style: subheaderStyle },
            { children: "Event Webcasts" }
          ),
          "eventWebcastsHeader"
        )
      );
      allWebcastItems = allWebcastItems.concat(webcastItems);
    }
    if (offlineWebcastItems.length !== 0) {
      if (webcastItems.length !== 0) {
        allWebcastItems.push(
          jsx_runtime_1.jsx(
            Divider_1.default,
            {},
            "offlineEventWebcastsDivider"
          )
        );
      }
      allWebcastItems.push(
        jsx_runtime_1.jsx(
          Subheader_1.default,
          Object.assign(
            { style: subheaderStyle },
            { children: "Offline Event Webcasts" }
          ),
          "offlineWebcastsHeader"
        )
      );
      allWebcastItems = allWebcastItems.concat(offlineWebcastItems);
    }
    if (offlineSpecialWebcastItems.length !== 0) {
      if (offlineWebcastItems.length !== 0) {
        allWebcastItems.push(
          jsx_runtime_1.jsx(
            Divider_1.default,
            {},
            "offlineSpecialWebcastsDivider"
          )
        );
      }
      allWebcastItems.push(
        jsx_runtime_1.jsx(
          Subheader_1.default,
          Object.assign(
            { style: subheaderStyle },
            { children: "Offline Special Webcasts" }
          ),
          "offlineSpecialWebcastsHeader"
        )
      );
      allWebcastItems = allWebcastItems.concat(offlineSpecialWebcastItems);
    }
    if (allWebcastItems.length === 0) {
      // No more webcasts, indicate that
      allWebcastItems.push(
        jsx_runtime_1.jsx(
          List_1.ListItem,
          { primaryText: "No more webcasts available", disabled: true },
          "nullWebcastsListItem"
        )
      );
    }
    const actions = [
      jsx_runtime_1.jsx(
        FlatButton_1.default,
        {
          label: "Cancel",
          onClick: () => this.onRequestClose(),
          primary: true,
        },
        void 0
      ),
    ];
    const titleStyle = {
      padding: 16,
    };
    const bodyStyle = {
      padding: 0,
    };
    return jsx_runtime_1.jsx(
      Dialog_1.default,
      Object.assign(
        {
          title: "Select a webcast",
          actions: actions,
          modal: false,
          titleStyle: titleStyle,
          bodyStyle: bodyStyle,
          open: this.props.open,
          onRequestClose: () => this.onRequestClose(),
          autoScrollBodyContent: true,
        },
        {
          children: jsx_runtime_1.jsx(
            List_1.List,
            { children: allWebcastItems },
            void 0
          ),
        }
      ),
      void 0
    );
  }
}
exports.default = WebcastSelectionDialog;
