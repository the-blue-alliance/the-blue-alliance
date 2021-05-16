"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
// @ts-expect-error ts-migrate(7022) FIXME: 'LampIcon' implicitly has type 'any' because it do... Remove this comment to see the full error message
const LampIcon = (props) => {
  const { width, height } = props;
  return jsx_runtime_1.jsx(
    "svg",
    Object.assign(
      {
        xmlns: "http://www.w3.org/2000/svg",
        width: width,
        height: height,
        viewBox: "0 0 240 240",
      },
      {
        children: jsx_runtime_1.jsxs(
          "g",
          Object.assign(
            { transform: "matrix(1.25,0,0,-1.25,0,240)" },
            {
              children: [
                jsx_runtime_1.jsx(
                  "path",
                  {
                    style: {
                      fill: "none",
                      stroke: "#ffffff",
                      strokeWidth: 6,
                      strokeLinecap: "butt",
                      strokeOpacity: 1,
                    },
                    d: "M 71,132 71,68",
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(
                  "path",
                  {
                    style: {
                      fill: "none",
                      stroke: "#ffffff",
                      strokeWidth: 6,
                      strokeLinecap: "butt",
                      strokeOpacity: 1,
                    },
                    d: "m 121,132 0,-64",
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(
                  "path",
                  {
                    style: {
                      fill: "none",
                      stroke: "#ffffff",
                      strokeWidth: 6,
                      strokeLinecap: "butt",
                      strokeOpacity: 1,
                    },
                    d: "M 71,68 C 71,54.182 82.182,43 96,43",
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(
                  "path",
                  {
                    style: {
                      fill: "none",
                      stroke: "#ffffff",
                      strokeWidth: 6,
                      strokeLinecap: "butt",
                      strokeOpacity: 1,
                    },
                    d: "M 121,68 C 121,54.182 109.818,43 96,43",
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(
                  "path",
                  {
                    style: {
                      fill: "none",
                      stroke: "#ffffff",
                      strokeWidth: 6,
                      strokeLinecap: "butt",
                      strokeOpacity: 1,
                    },
                    d: "M 96,132 96,43",
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(
                  "path",
                  {
                    style: {
                      fill: "none",
                      stroke: "#ffffff",
                      strokeWidth: 6,
                      strokeLinecap: "butt",
                      strokeOpacity: 1,
                    },
                    d: "m 71,71 50,0",
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(
                  "path",
                  {
                    style: {
                      fill: "none",
                      stroke: "#ffffff",
                      strokeWidth: 6,
                      strokeLinecap: "butt",
                      strokeOpacity: 1,
                    },
                    d: "m 71,99 50,0",
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(
                  "path",
                  {
                    style: {
                      fill: "#ffffff",
                      stroke: "none",
                      fillRule: "nonzero",
                    },
                    d: "m 132,128 c 0,-2.2 -1.8,-4 -4,-4 l -64,0 c -2.2,0 -4,1.8 -4,4 l 0,20 c 0,2.2 1.8,4 4,4 l 64,0 c 2.2,0 4,-1.8 4,-4 l 0,-20 z",
                  },
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
};
LampIcon.defaultProps = {
  width: 48,
  height: 48,
};
exports.default = LampIcon;
