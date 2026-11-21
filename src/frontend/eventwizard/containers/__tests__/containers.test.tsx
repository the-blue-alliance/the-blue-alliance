/* @jest-environment jsdom */
import React from "react";
import { act, render } from "@testing-library/react";
import { Provider } from "react-redux";
import { createStore, Store } from "redux";
import eventwizardReducer, { RootState } from "../../reducers";
import { updateAuth, setEvent, setManualEvent } from "../../actions";
import makeTrustedApiRequest from "../../net/TrustedApiRequest";
import makeApiV3Request from "../../net/ApiV3Request";

import AuthInput from "../../components/AuthInput";
import AuthTools from "../../components/AuthTools";
import EventSelector from "../../components/EventSelector";
import AwardsTab from "../../components/awardsTab/AwardsTab";
import EventAlliancesTab from "../../components/eventAlliances/EventAlliancesTab";
import EventInfoTab from "../../components/infoTab/EventInfoTab";
import EventMatchResultsTab from "../../components/eventMatchResultsTab/EventMatchResultsTab";
import EventRankingsTab from "../../components/eventRankingsTab/EventRankingsTab";
import EventScheduleTab from "../../components/eventScheduleTab/EventScheduleTab";
import FmsCompanionTab from "../../components/fmsCompanionTab/FmsCompanionTab";
import MatchVideosTab from "../../components/matchVideosTab/MatchVideosTab";
import TeamListTab from "../../components/teamsTab/TeamListTab";

import AuthInputContainer from "../AuthInputContainer";
import AuthToolsContainer from "../AuthToolsContainer";
import EventSelectorContainer from "../EventSelectorContainer";
import AwardsTabContainer from "../AwardsTabContainer";
import EventAlliancesTabContainer from "../EventAlliancesTabContainer";
import EventInfoContainer from "../EventInfoContainer";
import EventMatchResultsTabContainer from "../EventMatchResultsTabContainer";
import EventRankingsTabContainer from "../EventRankingsTabContainer";
import EventScheduleTabContainer from "../EventScheduleTabContainer";
import FmsCompanionContainer from "../FmsCompanionContainer";
import MatchVideosContainer from "../MatchVideosContainer";
import TeamListContainer from "../TeamListContainer";

jest.mock("../../net/TrustedApiRequest");
jest.mock("../../net/ApiV3Request");

// Replace every wrapped component with a spy so the props each container
// computes can be inspected directly.
jest.mock("../../components/AuthInput", () => jest.fn(() => null));
jest.mock("../../components/AuthTools", () => jest.fn(() => null));
jest.mock("../../components/EventSelector", () => jest.fn(() => null));
jest.mock("../../components/awardsTab/AwardsTab", () => jest.fn(() => null));
jest.mock("../../components/eventAlliances/EventAlliancesTab", () =>
  jest.fn(() => null)
);
jest.mock("../../components/infoTab/EventInfoTab", () => jest.fn(() => null));
jest.mock("../../components/eventMatchResultsTab/EventMatchResultsTab", () =>
  jest.fn(() => null)
);
jest.mock("../../components/eventRankingsTab/EventRankingsTab", () =>
  jest.fn(() => null)
);
jest.mock("../../components/eventScheduleTab/EventScheduleTab", () =>
  jest.fn(() => null)
);
jest.mock("../../components/fmsCompanionTab/FmsCompanionTab", () =>
  jest.fn(() => null)
);
jest.mock("../../components/matchVideosTab/MatchVideosTab", () =>
  jest.fn(() => null)
);
jest.mock("../../components/teamsTab/TeamListTab", () => jest.fn(() => null));

const mockTrusted = makeTrustedApiRequest as jest.Mock;
const mockApiV3 = makeApiV3Request as jest.Mock;

const trustedResponse = { ok: true } as Response;
const apiV3Response = { ok: true, status: 200 } as Response;

describe("eventwizard containers", () => {
  let store: Store<RootState>;

  const lastProps = (component: unknown): any => {
    const mock = component as jest.Mock;
    return mock.mock.calls[mock.mock.calls.length - 1][0];
  };

  const renderWithStore = (ui: React.ReactElement): void => {
    render(<Provider store={store}>{ui}</Provider>);
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockTrusted.mockResolvedValue(trustedResponse);
    mockApiV3.mockResolvedValue(apiV3Response);
    store = createStore(eventwizardReducer);
    store.dispatch(updateAuth("auth-id", "auth-secret"));
    store.dispatch(setEvent("2025nysu"));
    store.dispatch(setManualEvent(true));
  });

  describe("AuthInputContainer", () => {
    it("maps auth state and dispatches updateAuth from setAuth", () => {
      renderWithStore(<AuthInputContainer />);
      const props = lastProps(AuthInput);
      expect(props).toMatchObject({
        authId: "auth-id",
        authSecret: "auth-secret",
        selectedEvent: "2025nysu",
        manualEvent: true,
      });

      act(() => {
        props.setAuth("new-id", "new-secret");
      });
      expect(store.getState().auth).toMatchObject({
        authId: "new-id",
        authSecret: "new-secret",
      });
    });
  });

  describe("AuthToolsContainer", () => {
    it("maps auth state and dispatches updateAuth from setAuth", () => {
      renderWithStore(<AuthToolsContainer />);
      const props = lastProps(AuthTools);
      expect(props).toMatchObject({
        authId: "auth-id",
        authSecret: "auth-secret",
        selectedEvent: "2025nysu",
        manualEvent: true,
      });

      act(() => {
        props.setAuth("tools-id", "tools-secret");
      });
      expect(store.getState().auth).toMatchObject({
        authId: "tools-id",
        authSecret: "tools-secret",
      });
    });
  });

  describe("EventSelectorContainer", () => {
    it("maps event state and dispatches the event actions", () => {
      renderWithStore(<EventSelectorContainer />);
      const props = lastProps(EventSelector);
      expect(props).toMatchObject({
        selectedEvent: "2025nysu",
        manualEvent: true,
      });

      act(() => {
        props.setEvent("2025other");
      });
      expect(store.getState().auth.selectedEvent).toBe("2025other");

      act(() => {
        props.setManualEvent(false);
      });
      expect(store.getState().auth.manualEvent).toBe(false);

      act(() => {
        props.clearAuth();
      });
      expect(store.getState().auth).toMatchObject({
        authId: "",
        authSecret: "",
      });
    });
  });

  describe.each([
    ["AwardsTabContainer", AwardsTabContainer, AwardsTab],
    [
      "EventAlliancesTabContainer",
      EventAlliancesTabContainer,
      EventAlliancesTab,
    ],
    ["EventRankingsTabContainer", EventRankingsTabContainer, EventRankingsTab],
    ["EventScheduleTabContainer", EventScheduleTabContainer, EventScheduleTab],
    ["FmsCompanionContainer", FmsCompanionContainer, FmsCompanionTab],
  ])("%s", (_name, Container, Component) => {
    it("maps selectedEvent and signs trusted requests with the stored auth", async () => {
      renderWithStore(<Container />);
      const props = lastProps(Component);
      expect(props.selectedEvent).toBe("2025nysu");

      await expect(
        props.makeTrustedRequest("/api/trusted/v1/path", "body")
      ).resolves.toBe(trustedResponse);
      expect(mockTrusted).toHaveBeenCalledWith(
        "auth-id",
        "auth-secret",
        "/api/trusted/v1/path",
        "body"
      );
    });

    it("falls back to empty auth credentials when none are stored", async () => {
      store = createStore(eventwizardReducer);
      renderWithStore(<Container />);
      const props = lastProps(Component);

      await props.makeTrustedRequest("/api/trusted/v1/path", "body");
      expect(mockTrusted).toHaveBeenCalledWith(
        "",
        "",
        "/api/trusted/v1/path",
        "body"
      );
    });
  });

  describe.each([
    [
      "EventMatchResultsTabContainer",
      EventMatchResultsTabContainer,
      EventMatchResultsTab,
    ],
    ["TeamListContainer", TeamListContainer, TeamListTab],
  ])("%s", (_name, Container, Component) => {
    it("provides both trusted and APIv3 request helpers", async () => {
      renderWithStore(<Container />);
      const props = lastProps(Component);
      expect(props.selectedEvent).toBe("2025nysu");

      await expect(
        props.makeTrustedRequest("/api/trusted/v1/path", "body")
      ).resolves.toBe(trustedResponse);
      expect(mockTrusted).toHaveBeenCalledWith(
        "auth-id",
        "auth-secret",
        "/api/trusted/v1/path",
        "body"
      );

      await expect(props.makeApiV3Request("/api/v3/path")).resolves.toBe(
        apiV3Response
      );
      expect(mockApiV3).toHaveBeenCalledWith("auth-id", "/api/v3/path");
    });

    it("falls back to empty auth credentials when none are stored", async () => {
      store = createStore(eventwizardReducer);
      renderWithStore(<Container />);
      const props = lastProps(Component);

      await props.makeTrustedRequest("/p", "b");
      await props.makeApiV3Request("/v3");
      expect(mockTrusted).toHaveBeenCalledWith("", "", "/p", "b");
      expect(mockApiV3).toHaveBeenCalledWith("", "/v3");
    });
  });

  describe("EventInfoContainer", () => {
    it("maps authId and selectedEvent alongside both request helpers", async () => {
      renderWithStore(<EventInfoContainer />);
      const props = lastProps(EventInfoTab);
      expect(props).toMatchObject({
        authId: "auth-id",
        selectedEvent: "2025nysu",
      });

      await props.makeTrustedRequest("/api/trusted/v1/path", "body");
      expect(mockTrusted).toHaveBeenCalledWith(
        "auth-id",
        "auth-secret",
        "/api/trusted/v1/path",
        "body"
      );

      await props.makeApiV3Request("/api/v3/path");
      expect(mockApiV3).toHaveBeenCalledWith("auth-id", "/api/v3/path");
    });

    it("falls back to empty auth credentials when none are stored", async () => {
      store = createStore(eventwizardReducer);
      renderWithStore(<EventInfoContainer />);
      const props = lastProps(EventInfoTab);

      await props.makeTrustedRequest("/p", "b");
      await props.makeApiV3Request("/v3");
      expect(mockTrusted).toHaveBeenCalledWith("", "", "/p", "b");
      expect(mockApiV3).toHaveBeenCalledWith("", "/v3");
    });
  });

  describe("MatchVideosContainer", () => {
    it("forwards the HTTP method to the trusted request, defaulting to POST", async () => {
      renderWithStore(<MatchVideosContainer />);
      const props = lastProps(MatchVideosTab);
      expect(props.selectedEvent).toBe("2025nysu");

      await props.makeTrustedRequest("/api/trusted/v1/path", "body");
      expect(mockTrusted).toHaveBeenCalledWith(
        "auth-id",
        "auth-secret",
        "/api/trusted/v1/path",
        "body",
        "POST"
      );

      await props.makeTrustedRequest("/api/trusted/v1/path", "body", "DELETE");
      expect(mockTrusted).toHaveBeenCalledWith(
        "auth-id",
        "auth-secret",
        "/api/trusted/v1/path",
        "body",
        "DELETE"
      );

      await props.makeApiV3Request("/api/v3/path");
      expect(mockApiV3).toHaveBeenCalledWith("auth-id", "/api/v3/path");
    });

    it("falls back to empty auth credentials when none are stored", async () => {
      store = createStore(eventwizardReducer);
      renderWithStore(<MatchVideosContainer />);
      const props = lastProps(MatchVideosTab);

      await props.makeTrustedRequest("/p", "b");
      await props.makeApiV3Request("/v3");
      expect(mockTrusted).toHaveBeenCalledWith("", "", "/p", "b", "POST");
      expect(mockApiV3).toHaveBeenCalledWith("", "/v3");
    });
  });
});
