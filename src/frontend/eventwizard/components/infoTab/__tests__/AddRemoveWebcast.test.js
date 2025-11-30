import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import AddRemoveWebcast from "../AddRemoveWebcast";

// Mock WebcastList component
jest.mock("../WebcastList", () => (props) => (
  <div
    data-testid="webcast-list"
    data-webcast-count={props.webcasts.length}
  />
));

describe("AddRemoveWebcast", () => {
  const mockAddWebcast = jest.fn();
  const mockRemoveWebcast = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders the form group", () => {
    const html = renderToStaticMarkup(
      <AddRemoveWebcast
        eventInfo={null}
        addWebcast={mockAddWebcast}
        removeWebcast={mockRemoveWebcast}
      />
    );
    expect(html).toContain("form-group row");
  });

  it("shows 'No webcasts found' when eventInfo is null", () => {
    const html = renderToStaticMarkup(
      <AddRemoveWebcast
        eventInfo={null}
        addWebcast={mockAddWebcast}
        removeWebcast={mockRemoveWebcast}
      />
    );
    expect(html).toContain("No webcasts found");
  });

  it("shows 'No webcasts found' when webcasts array is empty", () => {
    const eventInfo = {
      webcasts: [],
    };
    const html = renderToStaticMarkup(
      <AddRemoveWebcast
        eventInfo={eventInfo}
        addWebcast={mockAddWebcast}
        removeWebcast={mockRemoveWebcast}
      />
    );
    expect(html).toContain("No webcasts found");
  });

  it("renders WebcastList when webcasts exist", () => {
    const eventInfo = {
      webcasts: [
        { type: "twitch", channel: "frcgamesense" },
        { type: "youtube", channel: "thebluealliance" },
      ],
    };
    const html = renderToStaticMarkup(
      <AddRemoveWebcast
        eventInfo={eventInfo}
        addWebcast={mockAddWebcast}
        removeWebcast={mockRemoveWebcast}
      />
    );
    expect(html).toContain('data-testid="webcast-list"');
    expect(html).toContain('data-webcast-count="2"');
  });

  it("renders Webcast label", () => {
    const html = renderToStaticMarkup(
      <AddRemoveWebcast
        eventInfo={null}
        addWebcast={mockAddWebcast}
        removeWebcast={mockRemoveWebcast}
      />
    );
    expect(html).toContain("Webcast");
  });

  it("uses proper Bootstrap classes", () => {
    const html = renderToStaticMarkup(
      <AddRemoveWebcast
        eventInfo={null}
        addWebcast={mockAddWebcast}
        removeWebcast={mockRemoveWebcast}
      />
    );
    expect(html).toContain("col-sm-2");
    expect(html).toContain("col-sm-10");
    expect(html).toContain("control-label");
  });

  it("calls addWebcast with URL and date when button handler is invoked", () => {
    const eventInfo = { webcasts: [] };
    const component = new AddRemoveWebcast({
      eventInfo,
      addWebcast: mockAddWebcast,
      removeWebcast: mockRemoveWebcast,
    });
    
    // Set state directly instead of calling setState
    component.state.newWebcastUrl = "https://youtu.be/test123";
    component.state.newWebcastDate = "2025-03-02";
    component.onAddWebcastClick();
    
    expect(mockAddWebcast).toHaveBeenCalledWith("https://youtu.be/test123", "2025-03-02");
  });

  it("clears state after adding webcast", () => {
    const eventInfo = { webcasts: [] };
    const component = new AddRemoveWebcast({
      eventInfo,
      addWebcast: mockAddWebcast,
      removeWebcast: mockRemoveWebcast,
    });
    
    // Spy on setState to verify it's called with empty values
    const setStateSpy = jest.spyOn(component, 'setState');
    
    // Set state directly
    component.state.newWebcastUrl = "https://youtu.be/test";
    component.state.newWebcastDate = "2025-03-02";
    component.onAddWebcastClick();
    
    expect(setStateSpy).toHaveBeenCalledWith({
      newWebcastUrl: "",
      newWebcastDate: "",
    });
  });

  it("updates state when URL input changes", () => {
    const eventInfo = { webcasts: [] };
    const component = new AddRemoveWebcast({
      eventInfo,
      addWebcast: mockAddWebcast,
      removeWebcast: mockRemoveWebcast,
    });
    
    const setStateSpy = jest.spyOn(component, 'setState');
    component.onNewWebcastUrlChange({ target: { value: "https://youtu.be/abc" } });
    
    expect(setStateSpy).toHaveBeenCalledWith({ newWebcastUrl: "https://youtu.be/abc" });
  });

  it("updates state when date input changes", () => {
    const eventInfo = { webcasts: [] };
    const component = new AddRemoveWebcast({
      eventInfo,
      addWebcast: mockAddWebcast,
      removeWebcast: mockRemoveWebcast,
    });
    
    const setStateSpy = jest.spyOn(component, 'setState');
    component.onNewWebcastDateChange({ target: { value: "2025-03-02" } });
    
    expect(setStateSpy).toHaveBeenCalledWith({ newWebcastDate: "2025-03-02" });
  });
});
