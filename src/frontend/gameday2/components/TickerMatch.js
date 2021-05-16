"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const colors_1 = require("material-ui/styles/colors");
const TickerMatch = (props) => {
  const matchStyle = {
    backgroundColor: colors_1.black,
    height: "100%",
    width: "auto",
    borderRadius: 2,
    marginRight: 5,
    marginLeft: 5,
    paddingRight: 10,
    paddingLeft: 10,
    display: "inline-block",
    WebkitBoxShadow:
      "rgba(0, 0, 0, 0.5) 0px 1px 6px, rgba(0, 0, 0, 0.5) 0px 1px 4px",
    MozBoxShadow:
      "rgba(0, 0, 0, 0.5) 0px 1px 6px, rgba(0, 0, 0, 0.5) 0px 1px 4px",
    BoxShadow: "rgba(0, 0, 0, 0.5) 0px 1px 6px, rgba(0, 0, 0, 0.5) 0px 1px 4px",
  };
  const matchLabelStyle = {
    color: colors_1.white,
    fontSize: 16,
    width: "auto",
    display: "inline-block",
    lineHeight: "36px",
    marginRight: 10,
    float: "left",
  };
  const alliancesStyle = {
    display: "inline-block",
    height: "28px",
    width: "auto",
    float: "left",
    marginTop: 5,
    fontWeight: "bold",
  };
  const redAllianceStyle = {
    color: "#FF0000",
    fontSize: 13,
    width: "auto",
    height: "50%",
    display: "block",
    lineHeight: "13px",
  };
  const blueAllianceStyle = {
    color: "#0066FF",
    fontSize: 13,
    width: "auto",
    height: "50%",
    display: "block",
    lineHeight: "13px",
  };
  const match = props.match;
  // Set backgrounds
  if (match.w === "red") {
    // Red win
    matchStyle.backgroundColor = "#330000";
  } else if (match.w === "blue") {
    // Blue win
    matchStyle.backgroundColor = "#000033";
  } else if (match.r !== -1 && match.b !== -1) {
    // Tie
    matchStyle.backgroundColor = "#220022";
  } else if (props.hasFavorite) {
    matchStyle.backgroundColor = "#e6c100";
    matchLabelStyle.color = colors_1.black;
  }
  // Generate strings
  let compLevel = match.c.toUpperCase();
  compLevel = compLevel === "QM" ? "Q" : compLevel;
  const matchNumber =
    compLevel === "QF" || compLevel === "SF" || compLevel === "F"
      ? `${match.s}-${match.m}`
      : match.m;
  let matchLabel = `${compLevel}${matchNumber}`;
  if (props.isBlueZone) {
    matchLabel = `${match.event_key.substring(4).toUpperCase()} ${matchLabel}`;
  }
  let redScore = match.r;
  let blueScore = match.b;
  redScore = redScore === -1 ? "" : ` - ${redScore}`;
  blueScore = blueScore === -1 ? "" : ` - ${blueScore}`;
  return jsx_runtime_1.jsxs(
    "div",
    Object.assign(
      { style: matchStyle },
      {
        children: [
          jsx_runtime_1.jsx(
            "div",
            Object.assign({ style: matchLabelStyle }, { children: matchLabel }),
            void 0
          ),
          jsx_runtime_1.jsxs(
            "div",
            Object.assign(
              { style: alliancesStyle },
              {
                children: [
                  jsx_runtime_1.jsxs(
                    "div",
                    Object.assign(
                      { style: redAllianceStyle },
                      {
                        children: [
                          match.rt[0].substring(3),
                          ", ",
                          match.rt[1].substring(3),
                          ",",
                          " ",
                          match.rt[2].substring(3),
                          redScore,
                        ],
                      }
                    ),
                    void 0
                  ),
                  jsx_runtime_1.jsxs(
                    "div",
                    Object.assign(
                      { style: blueAllianceStyle },
                      {
                        children: [
                          match.bt[0].substring(3),
                          ", ",
                          match.bt[1].substring(3),
                          ",",
                          " ",
                          match.bt[2].substring(3),
                          blueScore,
                        ],
                      }
                    ),
                    void 0
                  ),
                ],
              }
            ),
            void 0
          ),
        ],
      }
    ),
    void 0
  );
};
exports.default = TickerMatch;
