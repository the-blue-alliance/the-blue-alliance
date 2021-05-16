"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const AppBarContainer_1 = __importDefault(
  require("../containers/AppBarContainer")
);
const MainContentContainer_1 = __importDefault(
  require("../containers/MainContentContainer")
);
const ChatSidebarContainer_1 = __importDefault(
  require("../containers/ChatSidebarContainer")
);
const HashtagSidebarContainer_1 = __importDefault(
  require("../containers/HashtagSidebarContainer")
);
const GamedayFrame = () =>
  jsx_runtime_1.jsxs(
    "div",
    Object.assign(
      { className: "gameday container-full" },
      {
        children: [
          jsx_runtime_1.jsx(AppBarContainer_1.default, {}, void 0),
          jsx_runtime_1.jsx(HashtagSidebarContainer_1.default, {}, void 0),
          jsx_runtime_1.jsx(ChatSidebarContainer_1.default, {}, void 0),
          jsx_runtime_1.jsx(MainContentContainer_1.default, {}, void 0),
        ],
      }
    ),
    void 0
  );
exports.default = GamedayFrame;
