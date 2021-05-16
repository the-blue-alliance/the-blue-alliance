"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'reac... Remove this comment to see the full error message
const react_addons_transition_group_1 = __importDefault(
  require("react-addons-transition-group")
);
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const List_1 = require("material-ui/List");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Paper_1 = __importDefault(require("material-ui/Paper"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const home_1 = __importDefault(require("material-ui/svg-icons/action/home"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const check_1 = __importDefault(
  require("material-ui/svg-icons/navigation/check")
);
const AnimatableContainer_1 = __importDefault(require("./AnimatableContainer"));
class ChatSelector extends react_1.default.Component {
  setTwitchChat(e, channel) {
    this.props.setTwitchChat(channel);
    this.props.onRequestClose();
  }
  render() {
    const chatItems = [];
    this.props.chats.forEach((chat) => {
      const isSelected = chat.channel === this.props.currentChat;
      const isDefault = chat.channel === this.props.defaultChat;
      const icon = isSelected
        ? jsx_runtime_1.jsx(check_1.default, {}, void 0)
        : null;
      let chatName = chat.name;
      if (chat.channel === "firstupdatesnow" && isDefault) {
        chatName = "TBA GameDay / FUN";
      } else if (chat.channel === "firstinspires" && isDefault) {
        chatName = "TBA GameDay / FIRST";
      }
      chatItems.push(
        jsx_runtime_1.jsx(
          List_1.ListItem,
          {
            primaryText: chatName,
            leftIcon: isDefault
              ? jsx_runtime_1.jsx(home_1.default, {}, void 0)
              : null,
            rightIcon: icon,
            onClick: (e) => this.setTwitchChat(e, chat.channel),
          },
          chat.channel
        )
      );
    });
    const overlayStyle = {
      width: "100%",
      height: "100%",
      background: "rgba(0,0,0,0.2)",
      position: "absolute",
      transition: "all 150ms ease-in",
      willChange: "opacity",
    };
    const listStyle = {
      width: "100%",
      position: "absolute",
      bottom: 0,
      transition: "all 150ms ease-in",
      willChange: "transform opacity",
      height: "90%",
      overflowY: "auto",
    };
    return jsx_runtime_1.jsxs(
      react_addons_transition_group_1.default,
      Object.assign(
        { component: "div" },
        {
          children: [
            this.props.open &&
              jsx_runtime_1.jsx(
                AnimatableContainer_1.default,
                {
                  style: overlayStyle,
                  // @ts-expect-error ts-migrate(2322) FIXME: Type '{ key: string; style: { width: string; heigh... Remove this comment to see the full error message
                  onClick: () => this.props.onRequestClose(),
                  beginStyle: {
                    opacity: 0,
                  },
                  endStyle: {
                    opacity: 1,
                  },
                },
                "overlay"
              ),
            this.props.open &&
              jsx_runtime_1.jsx(
                AnimatableContainer_1.default,
                Object.assign(
                  {
                    style: listStyle,
                    beginStyle: {
                      opacity: 0,
                      transform: "translate(0, 50%)",
                    },
                    endStyle: {
                      opacity: 1,
                      transform: "translate(0, 0)",
                    },
                  },
                  {
                    children: jsx_runtime_1.jsx(
                      Paper_1.default,
                      Object.assign(
                        { zDepth: 4 },
                        {
                          children: jsx_runtime_1.jsx(
                            List_1.List,
                            Object.assign(
                              { onClick: (e) => e.stopPropagation() },
                              { children: chatItems }
                            ),
                            void 0
                          ),
                        }
                      ),
                      void 0
                    ),
                  }
                ),
                "selector"
              ),
          ],
        }
      ),
      void 0
    );
  }
}
exports.default = ChatSelector;
