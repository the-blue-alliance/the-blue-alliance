"use strict";
var __createBinding =
  (this && this.__createBinding) ||
  (Object.create
    ? function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        Object.defineProperty(o, k2, {
          enumerable: true,
          get: function () {
            return m[k];
          },
        });
      }
    : function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        o[k2] = m[k];
      });
var __setModuleDefault =
  (this && this.__setModuleDefault) ||
  (Object.create
    ? function (o, v) {
        Object.defineProperty(o, "default", { enumerable: true, value: v });
      }
    : function (o, v) {
        o["default"] = v;
      });
var __importStar =
  (this && this.__importStar) ||
  function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null)
      for (var k in mod)
        if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k))
          __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
  };
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importStar(require("react"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'elem... Remove this comment to see the full error message
const element_resize_event_1 = __importDefault(require("element-resize-event"));
class AutoScale extends react_1.Component {
  constructor() {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1-2 arguments, but got 0.
    super();
    this.state = {
      wrapperSize: { width: 0, height: 0 },
      contentSize: { width: 0, height: 0 },
      scale: 1,
    };
  }
  componentDidMount() {
    const actualContent = this.content.children[0];
    this.updateState(
      Object.assign(Object.assign({}, this.state), {
        contentSize: {
          width: actualContent.offsetWidth,
          height: actualContent.offsetHeight,
        },
        wrapperSize: {
          width: this.wrapper.offsetWidth,
          height: this.wrapper.offsetHeight,
        },
      })
    );
    element_resize_event_1.default(actualContent, () => {
      this.updateState(
        Object.assign(Object.assign({}, this.state), {
          contentSize: {
            width: actualContent.offsetWidth,
            height: actualContent.offsetHeight,
          },
        })
      );
    });
    element_resize_event_1.default(this.wrapper, () => {
      this.updateState(
        Object.assign(Object.assign({}, this.state), {
          wrapperSize: {
            width: this.wrapper.offsetWidth,
            height: this.wrapper.offsetHeight,
          },
        })
      );
    });
  }
  updateState(newState) {
    const { maxHeight, maxWidth, maxScale } = this.props;
    const { wrapperSize, contentSize } = newState;
    let scale = Math.min(
      wrapperSize.width / contentSize.width,
      wrapperSize.height / contentSize.height
    );
    if (maxHeight) {
      scale = Math.min(scale, maxHeight / contentSize.height);
    }
    if (maxWidth) {
      scale = Math.min(scale, maxWidth / contentSize.width);
    }
    if (maxScale) {
      scale = Math.min(scale, maxScale);
    }
    this.setState(Object.assign(Object.assign({}, newState), { scale }));
  }
  render() {
    const { scale, contentSize } = this.state;
    const { children, wrapperClass, containerClass, contentClass } = this.props;
    const containerHeight = scale * contentSize.height;
    const containerWidth = scale * contentSize.width;
    return jsx_runtime_1.jsx(
      "div",
      Object.assign(
        {
          ref: (el) => {
            this.wrapper = el;
          },
          className: wrapperClass,
        },
        {
          children: jsx_runtime_1.jsx(
            "div",
            Object.assign(
              {
                className: containerClass,
                style: {
                  maxWidth: "100%",
                  overflow: "hidden",
                  width: `${containerWidth}px`,
                  height: `${containerHeight}px`,
                },
              },
              {
                children: jsx_runtime_1.jsx(
                  "div",
                  Object.assign(
                    {
                      ref: (el) => {
                        this.content = el;
                      },
                      className: contentClass,
                      style: {
                        transform: `scale(${scale})`,
                        transformOrigin: "0 0 0",
                      },
                    },
                    { children: react_1.default.Children.only(children) }
                  ),
                  void 0
                ),
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
exports.default = AutoScale;
AutoScale.defaultProps = {
  wrapperClass: "",
  containerClass: "",
  contentClass: "",
};
