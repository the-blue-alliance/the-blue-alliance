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
});
