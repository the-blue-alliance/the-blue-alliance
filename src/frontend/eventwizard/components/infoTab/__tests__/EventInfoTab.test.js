import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import EventInfoTab from "../EventInfoTab";

// Mock child components

jest.mock("../../../net/EnsureRequestSuccess", () => (response) => {
  if (!response.ok) {
    throw new Error("Request failed");
  }
  return response;
});

describe("EventInfoTab", () => {
  const mockMakeTrustedRequest = jest.fn();

  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
    delete global.fetch;
  });

  it("renders the main container with correct structure", () => {
    const html = renderToStaticMarkup(
      <EventInfoTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );
    expect(html).toContain('class="tab-pane active col-xs-12"');
    expect(html).toContain('id="info"');
    expect(html).toContain("Event Info");
  });

  it("renders all child components", () => {
    const html = renderToStaticMarkup(
      <EventInfoTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );
    // Child components render their content (labels and inputs)
    expect(html).toContain("Playoff Type");
    expect(html).toContain("FIRST Sync Code");
    expect(html).toContain("Webcasts");
    expect(html).toContain("Team Mappings");
  });

  it("renders Publish Changes button", () => {
    const html = renderToStaticMarkup(
      <EventInfoTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );
    expect(html).toContain("Publish Changes");
  });

  it("disables Publish Changes button when eventInfo is null", () => {
    const html = renderToStaticMarkup(
      <EventInfoTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );
    expect(html).toContain("disabled");
  });

  it("shows primary button class by default", () => {
    const html = renderToStaticMarkup(
      <EventInfoTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );
    expect(html).toContain("btn-primary");
  });

  it("renders with proper row structure", () => {
    const html = renderToStaticMarkup(
      <EventInfoTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );
    expect(html).toContain('class="row"');
  });

  it("does not show status message initially", () => {
    const html = renderToStaticMarkup(
      <EventInfoTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );
    expect(html).not.toContain("Loading event info");
  });

  it("child components receive null eventInfo when selectedEvent is null", () => {
    const html = renderToStaticMarkup(
      <EventInfoTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );
    // When eventInfo is null, child inputs/selects are disabled
    expect(html).toContain("disabled");
    expect(html).toContain('aria-disabled="true"');
  });

  it("calls makeTrustedRequest when update button handler is invoked", () => {
    const eventInfo = {
      playoff_type: 0,
      first_code: "test_code",
      webcasts: [],
      remap_teams: {},
    };
    const component = new EventInfoTab({
      selectedEvent: "2024test",
      makeTrustedRequest: mockMakeTrustedRequest,
    });

    // Set eventInfo state
    component.state.eventInfo = eventInfo;
    component.updateEventInfo();

    expect(mockMakeTrustedRequest).toHaveBeenCalled();
  });
});
