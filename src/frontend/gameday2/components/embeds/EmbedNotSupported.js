"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const EmbedNotSupported = () => {
  const containerStyles = {
    margin: 20,
    textAlign: "center",
  };
  const textStyles = {
    color: "#ffffff",
  };
  return (
    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ margin: number; textAlign: string; }' is n... Remove this comment to see the full error message
    jsx_runtime_1.jsx(
      "div",
      Object.assign(
        { style: containerStyles },
        {
          children: jsx_runtime_1.jsx(
            "p",
            Object.assign(
              { style: textStyles },
              { children: "This webcast is not supported." }
            ),
            void 0
          ),
        }
      ),
      void 0
    )
  );
};
exports.default = EmbedNotSupported;
