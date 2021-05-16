"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    Object.defineProperty(o, k2, { enumerable: true, get: function() { return m[k]; } });
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
require("./gameday2.less");
const react_ga_1 = __importDefault(require("react-ga"));
const react_redux_1 = require("react-redux");
const redux_thunk_1 = __importDefault(require("redux-thunk"));
const redux_1 = require("redux");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'reac... Remove this comment to see the full error message
const react_dom_1 = __importDefault(require("react-dom"));
const query_string_1 = __importDefault(require("query-string"));
const MuiThemeProvider_1 = __importDefault(require("material-ui/styles/MuiThemeProvider"));
const colors_1 = require("material-ui/styles/colors");
const getMuiTheme_1 = __importDefault(require("material-ui/styles/getMuiTheme"));
const GamedayFrame_1 = __importDefault(require("./components/GamedayFrame"));
const reducers_1 = __importStar(require("./reducers"));
const actions_1 = require("./actions");
const LayoutConstants_1 = require("./constants/LayoutConstants");
react_ga_1.default.initialize("UA-1090782-9");
// @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
const webcastData = JSON.parse(document.getElementById("webcasts_json").innerHTML);
// @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
const defaultChat = document.getElementById("default_chat").innerHTML;
const store = (0, redux_1.createStore)(reducers_1.default, (0, redux_1.compose)((0, redux_1.applyMiddleware)(redux_thunk_1.default), window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__()));
reducers_1.firedux.dispatch = store.dispatch;
const muiTheme = (0, getMuiTheme_1.default)({
    palette: {
        primary1Color: colors_1.indigo500,
        primary2Color: colors_1.indigo700,
    },
    // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ palette: { primary1Color: stri... Remove this comment to see the full error message
    layout: {
        appBarHeight: 36,
        socialPanelWidth: 300,
        chatPanelWidth: 300,
    },
});
react_dom_1.default.render((0, jsx_runtime_1.jsx)(MuiThemeProvider_1.default, Object.assign({ muiTheme: muiTheme }, { children: (0, jsx_runtime_1.jsx)(react_redux_1.Provider, Object.assign({ store: store }, { children: (0, jsx_runtime_1.jsx)(GamedayFrame_1.default, {}, void 0) }), void 0) }), void 0), document.getElementById("content"));
// Subscribe to changes in state.videoGrid.displayed to watch the correct Firebase paths
// Subscribe to changes in state.videoGrid.domOrderLivescoreOn to watch the correct Firebase paths
let lastDisplayed = [];
const subscribedEvents = new Set();
const lastLivescores = new Set();
store.subscribe(() => {
    const state = store.getState();
    // See what got added or removed
    const a = new Set(lastDisplayed);
    const b = new Set(state.videoGrid.displayed);
    const added = new Set([...b].filter((x) => !a.has(x)));
    const removed = new Set([...a].filter((x) => !b.has(x)));
    // Subscribe to added event if not already added
    added.forEach((webcastKey) => {
        // @ts-expect-error ts-migrate(2538) FIXME: Type 'unknown' cannot be used as an index type.
        const eventKey = state.webcastsById[webcastKey].key;
        if (!subscribedEvents.has(eventKey)) {
            subscribedEvents.add(eventKey);
            reducers_1.firedux.watch(`e/${eventKey}/m`);
        }
    });
    // Unsubscribe from removed event if no more existing
    removed.forEach((webcastKey) => {
        const existingEventKeys = new Set();
        // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
        state.videoGrid.displayed.forEach((displayed) => existingEventKeys.add(state.webcastsById[displayed].key));
        // @ts-expect-error ts-migrate(2538) FIXME: Type 'unknown' cannot be used as an index type.
        const eventKey = state.webcastsById[webcastKey].key;
        if (!existingEventKeys.has(eventKey)) {
            subscribedEvents.delete(eventKey);
            reducers_1.firedux.ref.child(`e/${eventKey}/m`).off("value");
            reducers_1.firedux.watching[`e/${eventKey}/m`] = false; // To make firedux.watch work again
        }
    });
    // Something changed - save lastDisplayed
    if (added.size > 0 || removed.size > 0) {
        lastDisplayed = state.videoGrid.displayed;
    }
    // Update Livescore subscriptions
    const currentLivescores = new Set();
    state.videoGrid.domOrder.forEach((webcastKey, i) => {
        if (webcastKey && state.videoGrid.domOrderLivescoreOn[i]) {
            // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
            const eventKey = state.webcastsById[webcastKey].key;
            currentLivescores.add(eventKey);
        }
    });
    const addedLivescores = new Set([...currentLivescores].filter((x) => !lastLivescores.has(x)));
    const removedLivescores = new Set([...lastLivescores].filter((x) => !currentLivescores.has(x)));
    addedLivescores.forEach((eventKey) => {
        lastLivescores.add(eventKey);
        reducers_1.firedux.watch(`le/${eventKey}`);
    });
    removedLivescores.forEach((eventKey) => {
        lastLivescores.delete(eventKey);
        reducers_1.firedux.ref.child(`le/${eventKey}`).off("value");
        reducers_1.firedux.watching[`le/${eventKey}`] = false; // To make firedux.watch work again
    });
});
// Load any special webcasts
// @ts-expect-error ts-migrate(2345) FIXME: Argument of type '(dispatch: any, getState: any) =... Remove this comment to see the full error message
store.dispatch((0, actions_1.setWebcastsRaw)(webcastData));
// Restore layout from URL hash.
const params = query_string_1.default.parse(location.hash);
// @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'string | string[]' is not assign... Remove this comment to see the full error message
if (params.layout && Number.isInteger(Number.parseInt(params.layout, 10))) {
    // @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'string | string[]' is not assign... Remove this comment to see the full error message
    store.dispatch((0, actions_1.setLayout)(Number.parseInt(params.layout, 10)));
}
// Used to store webcast state. Hacky. 2017-03-01 -fangeugene
// ongoing_events_w_webcasts and special_webcasts should be separate
let specialWebcasts = webcastData.special_webcasts;
let ongoingEventsWithWebcasts = [];
// Subscribe to updates to special webcasts
reducers_1.firedux.ref.child("special_webcasts").on("value", (snapshot) => {
    specialWebcasts = snapshot.val();
    const webcasts = {
        ongoing_events_w_webcasts: ongoingEventsWithWebcasts,
        special_webcasts: specialWebcasts,
    };
    // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '(dispatch: any, getState: any) =... Remove this comment to see the full error message
    store.dispatch((0, actions_1.setWebcastsRaw)(webcasts));
});
// Subscribe to live events for webcasts
let isLoad = true;
reducers_1.firedux.ref.child("live_events").on("value", (snapshot) => {
    ongoingEventsWithWebcasts = [];
    const liveEvents = snapshot.val();
    if (liveEvents != null) {
        Object.values(liveEvents).forEach((event) => {
            if (event.webcasts) {
                ongoingEventsWithWebcasts.push(event);
            }
        });
        const webcasts = {
            ongoing_events_w_webcasts: ongoingEventsWithWebcasts,
            special_webcasts: specialWebcasts,
        };
        // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '(dispatch: any, getState: any) =... Remove this comment to see the full error message
        store.dispatch((0, actions_1.setWebcastsRaw)(webcasts));
    }
    // Now that webcasts are loaded, attempt to restore any state that's present in
    // the URL hash. Only run the first time.
    if (isLoad) {
        for (let i = 0; i < LayoutConstants_1.MAX_SUPPORTED_VIEWS; i++) {
            const viewKey = `view_${i}`;
            if (params[viewKey]) {
                // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '(dispatch: any, getState: any) =... Remove this comment to see the full error message
                store.dispatch((0, actions_1.addWebcastAtPosition)(params[viewKey], i));
            }
            const livescoreKey = `livescore_${i}`;
            if (params[livescoreKey]) {
                store.dispatch((0, actions_1.togglePositionLivescore)(i));
            }
        }
        // Set the default chat channel
        if (defaultChat) {
            store.dispatch((0, actions_1.setDefaultTwitchChat)(defaultChat));
            store.dispatch((0, actions_1.setTwitchChat)(defaultChat));
        }
        // Hide the chat if requested
        if (params.chat === "hidden") {
            store.dispatch((0, actions_1.setChatSidebarVisibility)(false));
        }
        else if (params.chat) {
            // Overwrite default chat with param
            store.dispatch((0, actions_1.setTwitchChat)(params.chat));
        }
        isLoad = false;
    }
});
// Subscribe to the store to keep the url hash in sync
store.subscribe(() => {
    const newParams = {};
    const state = store.getState();
    const { videoGrid: { layoutId, layoutSet, positionMap, domOrder, domOrderLivescoreOn, }, chats: { currentChat }, visibility: { chatSidebar }, } = state;
    // Which layout is currently active
    if (layoutSet) {
        newParams.layout = layoutId;
    }
    // Positions of all webcasts
    for (let i = 0; i < positionMap.length; i++) {
        if (domOrder[positionMap[i]]) {
            // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
            newParams[`view_${i}`] = domOrder[positionMap[i]];
        }
        if (domOrderLivescoreOn[positionMap[i]]) {
            // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
            newParams[`livescore_${i}`] = true;
        }
    }
    // Chat sidebar
    if (chatSidebar) {
        newParams.chat = currentChat;
    }
    else {
        newParams.chat = "hidden";
    }
    const query = query_string_1.default.stringify(newParams);
    if (query) {
        location.replace(`#${query}`);
    }
});
// Load myTBA Favorites
fetch("/_/account/favorites/1", {
    credentials: "same-origin",
})
    .then((response) => {
    if (response.status === 200) {
        return response.json();
    }
    return [];
})
    .then((json) => store.dispatch((0, actions_1.setFavoriteTeams)(json)));
