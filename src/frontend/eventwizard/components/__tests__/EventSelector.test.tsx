import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import EventSelector from "../EventSelector";

// Mock react-select/async
jest.mock("react-select/async", () => (props: any) => (
  <div
    data-testid="async-select"
    data-name={props.name}
    data-placeholder={props.placeholder}
  >
    {props.value && props.value.label}
  </div>
));

describe("EventSelector", () => {
  const mockSetEvent = jest.fn();
  const mockSetManualEvent = jest.fn();
  const mockClearAuth = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders the event selector form group", () => {
    const html = renderToStaticMarkup(
      <EventSelector
        manualEvent={false}
        setEvent={mockSetEvent}
        setManualEvent={mockSetManualEvent}
        clearAuth={mockClearAuth}
      />
    );
    expect(html).toContain("form-group");
    expect(html).toContain("Select Event");
  });

  it("renders AsyncSelect component", () => {
    const html = renderToStaticMarkup(
      <EventSelector
        manualEvent={false}
        setEvent={mockSetEvent}
        setManualEvent={mockSetManualEvent}
        clearAuth={mockClearAuth}
      />
    );
    expect(html).toContain('data-testid="async-select"');
    expect(html).toContain('data-name="selectEvent"');
  });

  it("does not render manual event input when manualEvent is false", () => {
    const html = renderToStaticMarkup(
      <EventSelector
        manualEvent={false}
        setEvent={mockSetEvent}
        setManualEvent={mockSetManualEvent}
        clearAuth={mockClearAuth}
      />
    );
    expect(html).not.toContain('id="event_key"');
  });

  it("renders manual event input when manualEvent is true", () => {
    const html = renderToStaticMarkup(
      <EventSelector
        manualEvent={true}
        setEvent={mockSetEvent}
        setManualEvent={mockSetManualEvent}
        clearAuth={mockClearAuth}
      />
    );
    expect(html).toContain('id="event_key"');
    expect(html).toContain('placeholder="Event Key"');
  });

  it("renders form with proper bootstrap classes", () => {
    const html = renderToStaticMarkup(
      <EventSelector
        manualEvent={false}
        setEvent={mockSetEvent}
        setManualEvent={mockSetManualEvent}
        clearAuth={mockClearAuth}
      />
    );
    expect(html).toContain("col-sm-2");
    expect(html).toContain("col-sm-10");
    expect(html).toContain("control-label");
  });

  it("renders manual event input with form-control class", () => {
    const html = renderToStaticMarkup(
      <EventSelector
        manualEvent={true}
        setEvent={mockSetEvent}
        setManualEvent={mockSetManualEvent}
        clearAuth={mockClearAuth}
      />
    );
    expect(html).toContain("form-control");
  });

  it("calls callbacks when event is selected", () => {
    const component = new (EventSelector as any)({
      manualEvent: false,
      setEvent: mockSetEvent,
      setManualEvent: mockSetManualEvent,
      clearAuth: mockClearAuth,
    });
    component.onEventSelected({ value: "2024test", label: "2024 Test" });
    expect(mockClearAuth).toHaveBeenCalled();
    expect(mockSetManualEvent).toHaveBeenCalledWith(false);
    expect(mockSetEvent).toHaveBeenCalledWith("2024test");
  });

  it("handles Other selection correctly", () => {
    const component = new (EventSelector as any)({
      manualEvent: false,
      setEvent: mockSetEvent,
      setManualEvent: mockSetManualEvent,
      clearAuth: mockClearAuth,
    });
    component.onEventSelected({ value: "_other", label: "Other" });
    expect(mockClearAuth).toHaveBeenCalled();
    expect(mockSetManualEvent).toHaveBeenCalledWith(true);
    expect(mockSetEvent).toHaveBeenCalledWith("");
  });

  it("calls setEvent when manual event key changes after debounce", () => {
    jest.useFakeTimers();
    const component = new (EventSelector as any)({
      manualEvent: true,
      setEvent: mockSetEvent,
      setManualEvent: mockSetManualEvent,
      clearAuth: mockClearAuth,
    });
    component.onManualEventChange({ target: { value: "2024test" } });
    // Should not be called immediately
    expect(mockSetEvent).not.toHaveBeenCalled();
    // Fast-forward time by 500ms (the debounce delay)
    jest.advanceTimersByTime(500);
    // Now it should have been called
    expect(mockSetEvent).toHaveBeenCalledWith("2024test");
    jest.useRealTimers();
  });

  describe("loadEvents", () => {
    beforeEach(() => {
      // Clear the cache before each test
      (EventSelector as any).eventsCache = null;
      global.fetch = jest.fn();
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    it("adds Other option when user is logged in and has events", async () => {
      const mockEvents = [
        { value: "2024test1", label: "2024 Test Event 1" },
        { value: "2024test2", label: "2024 Test Event 2" },
      ];

      (global.fetch as jest.Mock).mockResolvedValue({
        status: 200,
        json: async () => mockEvents,
      });

      const result = await EventSelector.loadEvents("");

      expect(result).toHaveLength(3);
      expect(result[2]).toEqual({ value: "_other", label: "Other" });
    });

    it("adds Other option when user is not logged in (401)", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        status: 401,
      });

      const result = await EventSelector.loadEvents("");

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({ value: "_other", label: "Other" });
    });

    it("filters events based on search string", async () => {
      const mockEvents = [
        { value: "2024test1", label: "2024 Test Event 1" },
        { value: "2024test2", label: "2024 Another Event" },
      ];

      (global.fetch as jest.Mock).mockResolvedValue({
        status: 200,
        json: async () => mockEvents,
      });

      const result = await EventSelector.loadEvents("test");

      expect(result).toHaveLength(1);
      expect(result[0].label).toContain("Test");
    });

    it("includes Other option in search results when searching for 'other'", async () => {
      const mockEvents = [
        { value: "2024test1", label: "2024 Test Event 1" },
      ];

      (global.fetch as jest.Mock).mockResolvedValue({
        status: 200,
        json: async () => mockEvents,
      });

      const result = await EventSelector.loadEvents("other");

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({ value: "_other", label: "Other" });
    });

    it("uses cached events on subsequent calls", async () => {
      const mockEvents = [
        { value: "2024test1", label: "2024 Test Event 1" },
      ];

      (global.fetch as jest.Mock).mockResolvedValue({
        status: 200,
        json: async () => mockEvents,
      });

      // First call
      await EventSelector.loadEvents("");
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Second call should use cache
      await EventSelector.loadEvents("");
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it("Other option is present in cached results", async () => {
      const mockEvents = [
        { value: "2024test1", label: "2024 Test Event 1" },
      ];

      (global.fetch as jest.Mock).mockResolvedValue({
        status: 200,
        json: async () => mockEvents,
      });

      // First call
      const result1 = await EventSelector.loadEvents("");
      expect(result1[1]).toEqual({ value: "_other", label: "Other" });

      // Second call from cache
      const result2 = await EventSelector.loadEvents("");
      expect(result2[1]).toEqual({ value: "_other", label: "Other" });
    });
  });
});
