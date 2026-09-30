import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import EventWizardTabFrame from "../EventWizardTabFrame";

// Containers need a redux store; stub them so this test only covers the frame.
jest.mock("../../containers/EventInfoContainer", () => () => (
  <div data-testid="event-info" />
));
jest.mock("../../containers/TeamListContainer", () => () => (
  <div data-testid="team-list" />
));
jest.mock("../../containers/AwardsTabContainer", () => () => (
  <div data-testid="awards" />
));
jest.mock("../../containers/MatchVideosContainer", () => () => (
  <div data-testid="match-videos" />
));
jest.mock("../../containers/EventScheduleTabContainer", () => () => (
  <div data-testid="schedule" />
));
jest.mock("../../containers/EventMatchResultsTabContainer", () => () => (
  <div data-testid="match-results" />
));
jest.mock("../../containers/EventRankingsTabContainer", () => () => (
  <div data-testid="rankings" />
));
jest.mock("../../containers/EventAlliancesTabContainer", () => () => (
  <div data-testid="alliances" />
));
jest.mock("../../containers/FmsCompanionContainer", () => () => (
  <div data-testid="fms-companion" />
));

describe("EventWizardTabFrame", () => {
  it("renders a nav tab for every wizard section", () => {
    const html = renderToStaticMarkup(<EventWizardTabFrame />);
    expect(html).toContain("nav nav-tabs");
    [
      ["#info", "Event Info"],
      ["#teams", "Teams"],
      ["#schedule", "Match Schedule"],
      ["#matches", "Match Results"],
      ["#match-videos", "Match Videos"],
      ["#rankings", "Rankings"],
      ["#alliances", "Alliance Selections"],
      ["#awards", "Awards"],
      ["#fms-companion", "FMS Companion"],
    ].forEach(([href, label]) => {
      expect(html).toContain(`href="${href}"`);
      expect(html).toContain(label);
    });
  });

  it("marks the Event Info tab as active by default", () => {
    const html = renderToStaticMarkup(<EventWizardTabFrame />);
    expect(html).toContain('<li class="active"><a href="#info"');
  });

  it("renders every tab container inside the tab content", () => {
    const html = renderToStaticMarkup(<EventWizardTabFrame />);
    expect(html).toContain("tab-content row");
    [
      "event-info",
      "team-list",
      "schedule",
      "match-results",
      "match-videos",
      "rankings",
      "alliances",
      "awards",
      "fms-companion",
    ].forEach((testId) => {
      expect(html).toContain(`data-testid="${testId}"`);
    });
  });
});
