"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const RaisedButton_1 = __importDefault(require("material-ui/RaisedButton"));
exports.default = () =>
  jsx_runtime_1.jsxs(
    "div",
    Object.assign(
      { className: "no-webcasts-container" },
      {
        children: [
          jsx_runtime_1.jsx("h1", { children: "No webcasts found" }, void 0),
          jsx_runtime_1.jsx(
            "p",
            {
              children:
                "Looks like there aren't any events with webcasts this week. Check on The Blue Alliance for upcoming events!",
            },
            void 0
          ),
          jsx_runtime_1.jsx(
            RaisedButton_1.default,
            {
              href: "https://www.thebluealliance.com",
              label: "Go to The Blue Alliance",
            },
            void 0
          ),
        ],
      }
    ),
    void 0
  );
