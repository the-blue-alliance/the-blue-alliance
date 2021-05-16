"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
const AutoScale_1 = __importDefault(require("./AutoScale/AutoScale"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module '../.... Remove this comment to see the full error message
const PowerupCount_1 = __importDefault(
  require("../../liveevent/components/PowerupCount")
);
const CountWrapper_1 = __importDefault(require("./CountWrapper"));
class LivescoreDisplay extends react_1.default.PureComponent {
  constructor() {
    super(...arguments);
    this.state = {
      currentTime: undefined,
    };
    this.updateCurrentTime = () => {
      this.setState({ currentTime: new Date().getTime() / 1000 });
    };
  }
  componentDidMount() {
    this.updateCurrentTime();
    setInterval(this.updateCurrentTime, 10000);
  }
  render() {
    const { matches, matchState } = this.props;
    if (!matchState) {
      return jsx_runtime_1.jsx(
        "div",
        Object.assign(
          { className: "livescore-wrapper" },
          {
            children: jsx_runtime_1.jsx(
              "div",
              Object.assign(
                { className: "livescore-container" },
                {
                  children: jsx_runtime_1.jsx(
                    "div",
                    Object.assign(
                      { className: "livescore-display" },
                      { children: "Live match info not available" }
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
    let {
      m: mode,
      t: timeRemaining,
      rs: redScore,
      rfc: redForceCount,
      rfp: redForcePlayed,
      rlc: redLevitateCount,
      rlp: redLevitatePlayed,
      rbc: redBoostCount,
      rbp: redBoostPlayed,
      rswo: redSwitchOwned,
      rsco: redScaleOwned,
      rcp: redCurrentPowerup,
      rpt: redPowerupTimeRemaining,
      raq: redAutoQuest,
      rfb: redFaceTheBoss,
      bs: blueScore,
      bfc: blueForceCount,
      bfp: blueForcePlayed,
      blc: blueLevitateCount,
      blp: blueLevitatePlayed,
      bbc: blueBoostCount,
      bbp: blueBoostPlayed,
      bswo: blueSwitchOwned,
      bsco: blueScaleOwned,
      bcp: blueCurrentPowerup,
      bpt: bluePowerupTimeRemaining,
      baq: blueAutoQuest,
      bfb: blueFaceTheBoss,
    } = matchState;
    let match;
    let nextMatch;
    matches.forEach((m) => {
      // Find current match
      if (m.shortKey === matchState.mk) {
        match = m;
      }
      // Find next unplayed match after current match
      if (match && !nextMatch) {
        if (m.r === -1 && m.b === -1) {
          nextMatch = m;
        }
      }
    });
    let showETA = false;
    if (mode === "post_match" && match && match.r !== -1 && match.b !== -1) {
      // If match has been played, display next match and ETA
      match = nextMatch;
      showETA = true;
    } else if (mode === "pre_match") {
      // If match mode is pre_match, display match and ETA
      showETA = true;
    }
    if (!match) {
      return jsx_runtime_1.jsx(
        "div",
        Object.assign(
          { className: "livescore-wrapper" },
          {
            children: jsx_runtime_1.jsx(
              "div",
              Object.assign(
                { className: "livescore-container" },
                {
                  children: jsx_runtime_1.jsx(
                    "div",
                    Object.assign(
                      { className: "livescore-display" },
                      { children: "Live match info not available" }
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
    let etaStr = "";
    if (showETA) {
      // Reset to pre match defaults
      mode = "pre_match";
      timeRemaining = 0;
      redScore = 0;
      redForceCount = 0;
      redForcePlayed = false;
      redLevitateCount = 0;
      redLevitatePlayed = false;
      redBoostCount = 0;
      redBoostPlayed = false;
      redSwitchOwned = 0;
      redScaleOwned = 0;
      redCurrentPowerup = null;
      redPowerupTimeRemaining = null;
      redAutoQuest = false;
      redFaceTheBoss = false;
      blueScore = 0;
      blueForceCount = 0;
      blueForcePlayed = false;
      blueLevitateCount = 0;
      blueLevitatePlayed = false;
      blueBoostCount = 0;
      blueBoostPlayed = false;
      blueSwitchOwned = false;
      blueScaleOwned = false;
      blueCurrentPowerup = null;
      bluePowerupTimeRemaining = null;
      blueAutoQuest = false;
      blueFaceTheBoss = false;
      if (this.state.currentTime && match.pt) {
        // @ts-expect-error ts-migrate(2532) FIXME: Object is possibly 'undefined'.
        const etaMin = (match.pt - this.state.currentTime) / 60;
        if (etaMin < 2) {
          etaStr = " in <2 min";
        } else if (etaMin > 120) {
          etaStr = ` in ~${Math.round(etaMin / 60)} h`;
        } else {
          etaStr = ` in ~${Math.round(etaMin)} min`;
        }
      } else {
        etaStr = " is next";
      }
    }
    let compLevel = match.c.toUpperCase();
    compLevel = compLevel === "QM" ? "Q" : compLevel;
    const matchNumber =
      compLevel === "QF" || compLevel === "SF" || compLevel === "F"
        ? `${match.s}-${match.m}`
        : match.m;
    const matchLabel = `${compLevel}${matchNumber}${etaStr}`;
    let progressColor;
    if (mode === "post_match" || (timeRemaining === 0 && mode === "teleop")) {
      progressColor = "progress-bar-red";
    } else if (timeRemaining <= 30 && mode === "teleop") {
      progressColor = "progress-bar-yellow";
    } else {
      progressColor = "progress-bar-green";
    }
    let progressWidth;
    if (mode === "post_match") {
      progressWidth = "100%";
    } else if (mode === "teleop") {
      progressWidth = `${((150 - timeRemaining) * 100) / 150}%`;
    } else if (mode === "auto") {
      progressWidth = `${((15 - timeRemaining) * 100) / 150}%`;
    } else {
      progressWidth = "0%";
    }
    let currentPowerup = null;
    let powerupTimeRemaining = null;
    let powerupColor = null;
    if (redCurrentPowerup) {
      currentPowerup = redCurrentPowerup;
      powerupTimeRemaining = redPowerupTimeRemaining;
      powerupColor = "red";
    } else if (blueCurrentPowerup) {
      currentPowerup = blueCurrentPowerup;
      powerupTimeRemaining = bluePowerupTimeRemaining;
      powerupColor = "blue";
    }
    return jsx_runtime_1.jsx(
      AutoScale_1.default,
      Object.assign(
        {
          wrapperClass: "livescore-wrapper",
          containerClass: "livescore-container",
          maxWidth: 800,
        },
        {
          children: jsx_runtime_1.jsxs(
            "div",
            Object.assign(
              { className: "livescore-display" },
              {
                children: [
                  jsx_runtime_1.jsx("h3", { children: matchLabel }, void 0),
                  jsx_runtime_1.jsxs(
                    "div",
                    Object.assign(
                      { className: "col-container" },
                      {
                        children: [
                          jsx_runtime_1.jsxs(
                            "div",
                            Object.assign(
                              { className: "side-col" },
                              {
                                children: [
                                  jsx_runtime_1.jsx(
                                    "div",
                                    Object.assign(
                                      {
                                        className: `booleanIndicator ${
                                          redScaleOwned && "red"
                                        }`,
                                      },
                                      { children: "Scale" }
                                    ),
                                    void 0
                                  ),
                                  jsx_runtime_1.jsx(
                                    "div",
                                    Object.assign(
                                      {
                                        className: `booleanIndicator ${
                                          redSwitchOwned && "red"
                                        }`,
                                      },
                                      { children: "Switch" }
                                    ),
                                    void 0
                                  ),
                                  jsx_runtime_1.jsxs(
                                    "div",
                                    Object.assign(
                                      { className: "powerupsContainer" },
                                      {
                                        children: [
                                          jsx_runtime_1.jsx(
                                            PowerupCount_1.default,
                                            {
                                              color: "red",
                                              type: "force",
                                              count: redForceCount,
                                              played: redForcePlayed,
                                            },
                                            void 0
                                          ),
                                          jsx_runtime_1.jsx(
                                            PowerupCount_1.default,
                                            {
                                              color: "red",
                                              type: "levitate",
                                              count: redLevitateCount,
                                              played: redLevitatePlayed,
                                              isCenter: true,
                                            },
                                            void 0
                                          ),
                                          jsx_runtime_1.jsx(
                                            PowerupCount_1.default,
                                            {
                                              color: "red",
                                              type: "boost",
                                              count: redBoostCount,
                                              played: redBoostPlayed,
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
                                    Object.assign(
                                      {
                                        className: `booleanIndicator ${
                                          redAutoQuest && "red"
                                        }`,
                                      },
                                      { children: "Auto Quest" }
                                    ),
                                    void 0
                                  ),
                                  jsx_runtime_1.jsx(
                                    "div",
                                    Object.assign(
                                      {
                                        className: `booleanIndicator ${
                                          redFaceTheBoss && "red"
                                        }`,
                                      },
                                      { children: "Face The Boss" }
                                    ),
                                    void 0
                                  ),
                                ],
                              }
                            ),
                            void 0
                          ),
                          jsx_runtime_1.jsxs(
                            "div",
                            Object.assign(
                              { className: "mid-col" },
                              {
                                children: [
                                  jsx_runtime_1.jsxs(
                                    "div",
                                    Object.assign(
                                      { className: "progress" },
                                      {
                                        children: [
                                          jsx_runtime_1.jsx(
                                            "div",
                                            {
                                              className: `progress-bar ${progressColor}`,
                                              style: { width: progressWidth },
                                            },
                                            void 0
                                          ),
                                          jsx_runtime_1.jsx(
                                            "div",
                                            Object.assign(
                                              {
                                                className:
                                                  "timeRemainingContainer",
                                              },
                                              {
                                                children: jsx_runtime_1.jsx(
                                                  "span",
                                                  Object.assign(
                                                    {
                                                      className:
                                                        "timeRemaining",
                                                    },
                                                    { children: timeRemaining }
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
                                  jsx_runtime_1.jsxs(
                                    "div",
                                    Object.assign(
                                      { className: "scoreContainer" },
                                      {
                                        children: [
                                          jsx_runtime_1.jsxs(
                                            "div",
                                            Object.assign(
                                              { className: "redAlliance" },
                                              {
                                                children: [
                                                  match.rt.map((teamKey) => {
                                                    const teamNum =
                                                      teamKey.substring(3);
                                                    return jsx_runtime_1.jsx(
                                                      "div",
                                                      { children: teamNum },
                                                      teamKey
                                                    );
                                                  }),
                                                  jsx_runtime_1.jsx(
                                                    "div",
                                                    Object.assign(
                                                      {
                                                        className: "score red",
                                                      },
                                                      {
                                                        children:
                                                          jsx_runtime_1.jsx(
                                                            CountWrapper_1.default,
                                                            {
                                                              number: redScore,
                                                            },
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
                                          jsx_runtime_1.jsxs(
                                            "div",
                                            Object.assign(
                                              { className: "blueAlliance" },
                                              {
                                                children: [
                                                  match.bt.map((teamKey) => {
                                                    const teamNum =
                                                      teamKey.substring(3);
                                                    return jsx_runtime_1.jsx(
                                                      "div",
                                                      { children: teamNum },
                                                      teamKey
                                                    );
                                                  }),
                                                  jsx_runtime_1.jsx(
                                                    "div",
                                                    Object.assign(
                                                      {
                                                        className: "score blue",
                                                      },
                                                      {
                                                        children:
                                                          jsx_runtime_1.jsx(
                                                            CountWrapper_1.default,
                                                            {
                                                              number: blueScore,
                                                            },
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
                                        ],
                                      }
                                    ),
                                    void 0
                                  ),
                                  currentPowerup &&
                                    jsx_runtime_1.jsxs(
                                      "div",
                                      Object.assign(
                                        {
                                          className: `currentPowerup ${powerupColor}`,
                                        },
                                        {
                                          children: [
                                            jsx_runtime_1.jsx(
                                              "img",
                                              {
                                                src: `/images/2018_${currentPowerup}.png`,
                                                className: "currentPowerupIcon",
                                                role: "presentation",
                                              },
                                              void 0
                                            ),
                                            jsx_runtime_1.jsx("br", {}, void 0),
                                            powerupTimeRemaining,
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
                          jsx_runtime_1.jsxs(
                            "div",
                            Object.assign(
                              { className: "side-col" },
                              {
                                children: [
                                  jsx_runtime_1.jsx(
                                    "div",
                                    Object.assign(
                                      {
                                        className: `booleanIndicator ${
                                          blueScaleOwned && "blue"
                                        }`,
                                      },
                                      { children: "Scale" }
                                    ),
                                    void 0
                                  ),
                                  jsx_runtime_1.jsx(
                                    "div",
                                    Object.assign(
                                      {
                                        className: `booleanIndicator ${
                                          blueSwitchOwned && "blue"
                                        }`,
                                      },
                                      { children: "Switch" }
                                    ),
                                    void 0
                                  ),
                                  jsx_runtime_1.jsxs(
                                    "div",
                                    Object.assign(
                                      { className: "powerupsContainer" },
                                      {
                                        children: [
                                          jsx_runtime_1.jsx(
                                            PowerupCount_1.default,
                                            {
                                              color: "blue",
                                              type: "force",
                                              count: blueForceCount,
                                              played: blueForcePlayed,
                                            },
                                            void 0
                                          ),
                                          jsx_runtime_1.jsx(
                                            PowerupCount_1.default,
                                            {
                                              color: "blue",
                                              type: "levitate",
                                              count: blueLevitateCount,
                                              played: blueLevitatePlayed,
                                              isCenter: true,
                                            },
                                            void 0
                                          ),
                                          jsx_runtime_1.jsx(
                                            PowerupCount_1.default,
                                            {
                                              color: "blue",
                                              type: "boost",
                                              count: blueBoostCount,
                                              played: blueBoostPlayed,
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
                                    Object.assign(
                                      {
                                        className: `booleanIndicator ${
                                          blueAutoQuest && "blue"
                                        }`,
                                      },
                                      { children: "Auto Quest" }
                                    ),
                                    void 0
                                  ),
                                  jsx_runtime_1.jsx(
                                    "div",
                                    Object.assign(
                                      {
                                        className: `booleanIndicator ${
                                          blueFaceTheBoss && "blue"
                                        }`,
                                      },
                                      { children: "Face The Boss" }
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
exports.default = LivescoreDisplay;
