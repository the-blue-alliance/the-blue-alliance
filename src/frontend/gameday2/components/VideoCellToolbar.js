"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Toolbar_1 = require("material-ui/Toolbar");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const FlatButton_1 = __importDefault(require("material-ui/FlatButton"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const IconButton_1 = __importDefault(require("material-ui/IconButton"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const close_1 = __importDefault(
  require("material-ui/svg-icons/navigation/close")
);
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const compare_arrows_1 = __importDefault(
  require("material-ui/svg-icons/action/compare-arrows")
);
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const videocam_1 = __importDefault(
  require("material-ui/svg-icons/av/videocam")
);
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const equalizer_1 = __importDefault(
  require("material-ui/svg-icons/av/equalizer")
);
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const colors_1 = require("material-ui/styles/colors");
const TickerMatch_1 = __importDefault(require("./TickerMatch"));
const LayoutConstants_1 = require("../constants/LayoutConstants");
const VideoCellToolbar = (props) => {
  const toolbarStyle = Object.assign(
    { backgroundColor: colors_1.grey900 },
    props.style
  );
  const titleStyle = {
    color: colors_1.white,
    fontSize: 16,
    marginLeft: 0,
    marginRight: 0,
  };
  const matchTickerGroupStyle = {
    flexGrow: 1,
    width: "0%",
    overflow: "hidden",
    whiteSpace: "nowrap",
  };
  const matchTickerStyle = {
    overflow: "hidden",
    whiteSpace: "nowrap",
  };
  const controlsStyle = {
    position: "absolute",
    right: 0,
    marginRight: 0,
    backgroundColor: colors_1.grey900,
    boxShadow: "-2px 0px 15px -2px rgba(0, 0, 0, 0.5)",
  };
  // Create tickerMatches
  const tickerMatches = [];
  props.matches.forEach((match) => {
    // See if match has a favorite team
    let hasFavorite = false;
    const teamKeys = match.rt.concat(match.bt);
    teamKeys.forEach((teamKey) => {
      if (props.favoriteTeams.has(teamKey)) {
        hasFavorite = true;
      }
    });
    tickerMatches.push(
      jsx_runtime_1.jsx(
        TickerMatch_1.default,
        {
          match: match,
          hasFavorite: hasFavorite,
          isBlueZone: props.isBlueZone,
        },
        match.key
      )
    );
  });
  let swapButton;
  if (LayoutConstants_1.NUM_VIEWS_FOR_LAYOUT[props.layoutId] === 1) {
    swapButton = null;
  } else {
    swapButton = jsx_runtime_1.jsx(
      IconButton_1.default,
      Object.assign(
        {
          tooltip: "Swap position",
          tooltipPosition: "top-center",
          onClick: () => props.onRequestSwapPosition(),
          touch: true,
        },
        {
          children: jsx_runtime_1.jsx(
            compare_arrows_1.default,
            { color: colors_1.white },
            void 0
          ),
        }
      ),
      void 0
    );
  }
  return jsx_runtime_1.jsxs(
    Toolbar_1.Toolbar,
    Object.assign(
      { style: toolbarStyle },
      {
        children: [
          jsx_runtime_1.jsx(
            Toolbar_1.ToolbarGroup,
            {
              children: jsx_runtime_1.jsx(
                FlatButton_1.default,
                {
                  label: props.webcast.name,
                  style: titleStyle,
                  href: `/event/${props.webcast.key}`,
                  target: "_blank",
                  disabled: props.specialWebcastIds.has(props.webcast.id),
                },
                void 0
              ),
            },
            void 0
          ),
          jsx_runtime_1.jsx(
            Toolbar_1.ToolbarGroup,
            Object.assign(
              { style: matchTickerGroupStyle },
              {
                children: jsx_runtime_1.jsx(
                  "div",
                  Object.assign(
                    { style: matchTickerStyle },
                    { children: tickerMatches }
                  ),
                  void 0
                ),
              }
            ),
            void 0
          ),
          jsx_runtime_1.jsxs(
            Toolbar_1.ToolbarGroup,
            Object.assign(
              { lastChild: true, style: controlsStyle },
              {
                children: [
                  swapButton,
                  jsx_runtime_1.jsx(
                    IconButton_1.default,
                    Object.assign(
                      {
                        tooltip: "Change webcast",
                        tooltipPosition: "top-center",
                        onClick: () => props.onRequestSelectWebcast(),
                        touch: true,
                      },
                      {
                        children: jsx_runtime_1.jsx(
                          videocam_1.default,
                          { color: colors_1.white },
                          void 0
                        ),
                      }
                    ),
                    void 0
                  ),
                  jsx_runtime_1.jsx(
                    IconButton_1.default,
                    Object.assign(
                      {
                        tooltip: props.livescoreOn
                          ? "Switch to webcast view"
                          : "Switch to live scores view",
                        tooltipPosition: "top-center",
                        onClick: () => props.onRequestLiveScoresToggle(),
                        touch: true,
                      },
                      {
                        children: jsx_runtime_1.jsx(
                          equalizer_1.default,
                          {
                            color: props.livescoreOn
                              ? colors_1.green500
                              : colors_1.white,
                          },
                          void 0
                        ),
                      }
                    ),
                    void 0
                  ),
                  jsx_runtime_1.jsx(
                    IconButton_1.default,
                    Object.assign(
                      {
                        onClick: () => props.removeWebcast(props.webcast.id),
                        tooltip: "Close webcast",
                        tooltipPosition: "top-left",
                        touch: true,
                      },
                      {
                        children: jsx_runtime_1.jsx(
                          close_1.default,
                          { color: colors_1.white },
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
  );
};
exports.default = VideoCellToolbar;
