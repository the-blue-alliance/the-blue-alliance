"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
exports.firedux = void 0;
const app_1 = __importDefault(require("firebase/app"));
require("firebase/database");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'fire... Remove this comment to see the full error message
const firedux_1 = __importDefault(require("firedux"));
const redux_1 = require("redux");
const webcastsById_1 = require("./webcastsById");
const visibility_1 = __importDefault(require("./visibility"));
const videoGrid_1 = __importDefault(require("./videoGrid"));
const chats_1 = __importDefault(require("./chats"));
const favorites_1 = __importDefault(require("./favorites"));
// Firebase
const firebaseApp = app_1.default.initializeApp({
  apiKey: "AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs",
  authDomain: "tbatv-prod-hrd.firebaseapp.com",
  databaseURL: "https://tbatv-prod-hrd.firebaseio.com",
});
const ref = firebaseApp.database().ref();
exports.firedux = new firedux_1.default({
  ref,
});
const gamedayReducer = redux_1.combineReducers({
  firedux: exports.firedux.reducer(),
  webcastsById: webcastsById_1.webcastsById,
  specialWebcastIds: webcastsById_1.specialWebcastIds,
  visibility: visibility_1.default,
  videoGrid: videoGrid_1.default,
  chats: chats_1.default,
  favoriteTeams: favorites_1.default,
});
exports.default = gamedayReducer;
