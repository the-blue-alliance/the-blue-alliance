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
const Paper_1 = __importDefault(require("material-ui/Paper"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const List_1 = require("material-ui/List");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'reac... Remove this comment to see the full error message
const react_event_listener_1 = __importDefault(require("react-event-listener"));
const layoutUtils_1 = require("../utils/layoutUtils");
const LayoutConstants_1 = require("../constants/LayoutConstants");
class LayoutSelectionPanelMaterial extends react_1.default.Component {
  constructor(props) {
    super(props);
    this.layout = {
      margin: 20,
    };
  }
  componentDidMount() {
    this.updateSizing();
  }
  componentDidUpdate() {
    this.updateSizing();
  }
  updateSizing() {
    const component = this.component;
    const listContainer = this.listContainer;
    const list = this.list;
    let height = 0;
    height += list.offsetHeight;
    height += listContainer.previousSibling.offsetHeight;
    const maxHeight = component.offsetHeight - 2 * this.layout.margin;
    if (height > maxHeight) {
      let listContainerHeight = maxHeight;
      listContainerHeight -= listContainer.previousSibling.offsetHeight;
      listContainer.style.height = `${listContainerHeight}px`;
      listContainer.style.overflowY = "auto";
    } else {
      listContainer.style.height = null;
    }
  }
  render() {
    const layouts = [];
    for (let i = 0; i < LayoutConstants_1.NUM_LAYOUTS; i++) {
      const layoutNum = LayoutConstants_1.LAYOUT_DISPLAY_ORDER[i];
      layouts.push(
        jsx_runtime_1.jsx(
          List_1.ListItem,
          {
            primaryText: LayoutConstants_1.NAME_FOR_LAYOUT[layoutNum],
            onClick: () => this.props.setLayout(layoutNum),
            rightIcon: layoutUtils_1.getLayoutSvgIcon(layoutNum),
          },
          i.toString()
        )
      );
    }
    const componentStyle = {
      width: "100%",
      height: "100%",
    };
    const containerStyles = {
      width: "300px",
      maxWidth: "100%",
      margin: "auto",
      marginTop: `${this.layout.margin}px`,
    };
    const titleStyle = {
      padding: "16px",
      fontSize: "22px",
      margin: 0,
      fontWeight: 400,
      borderBottom: "1px solid rgb(224, 224, 224)",
    };
    return jsx_runtime_1.jsx(
      "div",
      Object.assign(
        {
          style: componentStyle,
          ref: (e) => {
            this.component = e;
          },
        },
        {
          children: jsx_runtime_1.jsxs(
            Paper_1.default,
            Object.assign(
              { style: containerStyles },
              {
                children: [
                  jsx_runtime_1.jsx(
                    react_event_listener_1.default,
                    { target: "window", onResize: () => this.updateSizing() },
                    void 0
                  ),
                  jsx_runtime_1.jsx(
                    "h3",
                    Object.assign(
                      { style: titleStyle },
                      { children: "Select a layout" }
                    ),
                    void 0
                  ),
                  jsx_runtime_1.jsx(
                    "div",
                    Object.assign(
                      {
                        ref: (e) => {
                          this.listContainer = e;
                        },
                      },
                      {
                        children: jsx_runtime_1.jsx(
                          "div",
                          Object.assign(
                            {
                              ref: (e) => {
                                this.list = e;
                              },
                            },
                            {
                              children: jsx_runtime_1.jsx(
                                List_1.List,
                                { children: layouts },
                                void 0
                              ),
                            }
                          ),
                          void 0
                        ),
                      }
                    ),
                    void 0
                  ),
                ],
              }
            ),
            void 0
          ),
        }
      ),
      void 0
    );
  }
}
exports.default = LayoutSelectionPanelMaterial;
