"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Card_1 = require("material-ui/Card");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const RaisedButton_1 = __importDefault(require("material-ui/RaisedButton"));
const EmbedDirectLink = (props) => {
  const directLink = props.webcast.channel;
  const style = {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translateX(-50%) translateY(-50%)",
  };
  return jsx_runtime_1.jsxs(
    Card_1.Card,
    Object.assign(
      { style: style },
      {
        children: [
          jsx_runtime_1.jsx(
            Card_1.CardHeader,
            { title: "Webcast could not be embedded" },
            void 0
          ),
          jsx_runtime_1.jsx(
            Card_1.CardText,
            {
              children:
                "Due to technical or copyright issues, the webcast cannot be displayed in TBA GameDay.",
            },
            void 0
          ),
          jsx_runtime_1.jsx(
            Card_1.CardActions,
            {
              children: jsx_runtime_1.jsx(
                RaisedButton_1.default,
                {
                  href: directLink,
                  target: "_blank",
                  label: "Open in new tab",
                },
                void 0
              ),
            },
            void 0
          ),
        ],
      }
    ),
    void 0
  );
};
exports.default = EmbedDirectLink;
