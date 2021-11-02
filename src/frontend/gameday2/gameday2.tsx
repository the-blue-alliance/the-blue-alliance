import "./gameday2.less";
import React from "react";
import ReactGA from "react-ga";
import { Provider } from "react-redux";
import thunk from "redux-thunk";
import { createStore, applyMiddleware, compose } from "redux";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'reac... Remove this comment to see the full error message
import ReactDOM from "react-dom";
import queryString from "query-string";
import MuiThemeProvider from "material-ui/styles/MuiThemeProvider";
import { indigo500, indigo700 } from "material-ui/styles/colors";
import getMuiTheme from "material-ui/styles/getMuiTheme";
import GamedayFrame from "./components/GamedayFrame";
import gamedayReducer, { firedux } from "./reducers";
import { setWebcastsRaw, setLayout, addWebcastAtPosition, setTwitchChat, setDefaultTwitchChat, setChatSidebarVisibility, setFavoriteTeams, togglePositionLivescore, } from "./actions";
import { MAX_SUPPORTED_VIEWS } from "./constants/LayoutConstants";
ReactGA.initialize("UA-1090782-9");
// @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
const webcastData = JSON.parse(document.getElementById("webcasts_json").innerHTML);
// @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
const defaultChat = document.getElementById("default_chat").innerHTML;
const store = createStore(gamedayReducer, compose(applyMiddleware(thunk), (window as any).__REDUX_DEVTOOLS_EXTENSION__ && (window as any).__REDUX_DEVTOOLS_EXTENSION__()));
firedux.dispatch = store.dispatch;
const muiTheme = getMuiTheme({
    palette: {
        primary1Color: indigo500,
        primary2Color: indigo700,
    },
    // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ palette: { primary1Color: stri... Remove this comment to see the full error message
    layout: {
        appBarHeight: 36,
        socialPanelWidth: 300,
        chatPanelWidth: 300,
    },
});
ReactDOM.render(<MuiThemeProvider muiTheme={muiTheme}>
    <Provider store={store}>
      <GamedayFrame />
    </Provider>
  </MuiThemeProvider>, document.getElementById("content"));
// Subscribe to changes in state.videoGrid.displayed to watch the correct Firebase paths
// Subscribe to changes in state.videoGrid.domOrderLivescoreOn to watch the correct Firebase paths
let lastDisplayed: any = [];
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
            firedux.watch(`e/${eventKey}/m`);
        }
    });
    // Unsubscribe from removed event if no more existing
    removed.forEach((webcastKey) => {
        const existingEventKeys = new Set();
        // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
        state.videoGrid.displayed.forEach((displayed: any) => existingEventKeys.add(state.webcastsById[displayed].key));
        // @ts-expect-error ts-migrate(2538) FIXME: Type 'unknown' cannot be used as an index type.
        const eventKey = state.webcastsById[webcastKey].key;
        if (!existingEventKeys.has(eventKey)) {
            subscribedEvents.delete(eventKey);
            firedux.ref.child(`e/${eventKey}/m`).off("value");
            firedux.watching[`e/${eventKey}/m`] = false; // To make firedux.watch work again
        }
    });
    // Something changed - save lastDisplayed
    if (added.size > 0 || removed.size > 0) {
        lastDisplayed = state.videoGrid.displayed;
    }
    // Update Livescore subscriptions
    const currentLivescores = new Set();
    state.videoGrid.domOrder.forEach((webcastKey: any, i: any) => {
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
        firedux.watch(`le/${eventKey}`);
    });
    removedLivescores.forEach((eventKey) => {
        lastLivescores.delete(eventKey);
        firedux.ref.child(`le/${eventKey}`).off("value");
        firedux.watching[`le/${eventKey}`] = false; // To make firedux.watch work again
    });
});
// Load any special webcasts
// @ts-expect-error ts-migrate(2345) FIXME: Argument of type '(dispatch: any, getState: any) =... Remove this comment to see the full error message
store.dispatch(setWebcastsRaw(webcastData));
// Restore layout from URL hash.
const params = queryString.parse(location.hash);
// @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'string | string[]' is not assign... Remove this comment to see the full error message
if (params.layout && Number.isInteger(Number.parseInt(params.layout, 10))) {
    // @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'string | string[]' is not assign... Remove this comment to see the full error message
    store.dispatch(setLayout(Number.parseInt(params.layout, 10)));
}
// Used to store webcast state. Hacky. 2017-03-01 -fangeugene
// ongoing_events_w_webcasts and special_webcasts should be separate
let specialWebcasts = webcastData.special_webcasts;
let ongoingEventsWithWebcasts: any = [];
// Subscribe to updates to special webcasts
firedux.ref.child("special_webcasts").on("value", (snapshot: any) => {
    specialWebcasts = snapshot.val();
    const webcasts = {
        ongoing_events_w_webcasts: ongoingEventsWithWebcasts,
        special_webcasts: specialWebcasts,
    };
    // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '(dispatch: any, getState: any) =... Remove this comment to see the full error message
    store.dispatch(setWebcastsRaw(webcasts));
});
// Subscribe to live events for webcasts
let isLoad = true;
firedux.ref.child("live_events").on("value", (snapshot: any) => {
    ongoingEventsWithWebcasts = [];
    const liveEvents = snapshot.val();
    if (liveEvents != null) {
        Object.values(liveEvents).forEach((event) => {
            if ((event as any).webcasts) {
                ongoingEventsWithWebcasts.push(event);
            }
        });
        const webcasts = {
            ongoing_events_w_webcasts: ongoingEventsWithWebcasts,
            special_webcasts: specialWebcasts,
        };
        // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '(dispatch: any, getState: any) =... Remove this comment to see the full error message
        store.dispatch(setWebcastsRaw(webcasts));
    }
    // Now that webcasts are loaded, attempt to restore any state that's present in
    // the URL hash. Only run the first time.
    if (isLoad) {
        for (let i = 0; i < MAX_SUPPORTED_VIEWS; i++) {
            const viewKey = `view_${i}`;
            if (params[viewKey]) {
                // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '(dispatch: any, getState: any) =... Remove this comment to see the full error message
                store.dispatch(addWebcastAtPosition(params[viewKey], i));
            }
            const livescoreKey = `livescore_${i}`;
            if (params[livescoreKey]) {
                store.dispatch(togglePositionLivescore(i));
            }
        }
        // Set the default chat channel
        if (defaultChat) {
            store.dispatch(setDefaultTwitchChat(defaultChat));
            store.dispatch(setTwitchChat(defaultChat));
        }
        // Hide the chat if requested
        if (params.chat === "hidden") {
            store.dispatch(setChatSidebarVisibility(false));
        }
        else if (params.chat) {
            // Overwrite default chat with param
            store.dispatch(setTwitchChat(params.chat));
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
        (newParams as any).layout = layoutId;
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
        (newParams as any).chat = currentChat;
    }
    else {
        (newParams as any).chat = "hidden";
    }
    const query = queryString.stringify(newParams);
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
    .then((json) => store.dispatch(setFavoriteTeams(json)));
