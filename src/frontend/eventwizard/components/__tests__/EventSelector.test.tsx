/* @jest-environment jsdom */
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventSelector from "../EventSelector";

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
    expect(html).toContain("selectEvent");
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
    expect(html).not.toContain('placeholder="Event Key"');
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
    expect(html).toContain('placeholder="Event Key"');
  });

  it("renders Select Event label", () => {
    const html = renderToStaticMarkup(
      <EventSelector
        manualEvent={false}
        setEvent={mockSetEvent}
        setManualEvent={mockSetManualEvent}
        clearAuth={mockClearAuth}
      />
    );
    expect(html).toContain("Select Event");
  });

  it("renders with correct form structure", () => {
    const html = renderToStaticMarkup(
      <EventSelector
        manualEvent={true}
        setEvent={mockSetEvent}
        setManualEvent={mockSetManualEvent}
        clearAuth={mockClearAuth}
      />
    );
    expect(html).toContain("form-group");
  });
});

describe("EventSelector interactions", () => {
  const mockSetEvent = jest.fn();
  const mockSetManualEvent = jest.fn();
  const mockClearAuth = jest.fn();
  const mockFetch = jest.fn();

  const apiEvents = [
    { value: "2025nysu", label: "2025 SUNY Regional" },
    { value: "2025nyro", label: "2025 Finger Lakes Regional" },
  ];

  const renderSelector = (manualEvent = false) =>
    render(
      <EventSelector
        manualEvent={manualEvent}
        selectedEvent=""
        setEvent={mockSetEvent}
        setManualEvent={mockSetManualEvent}
        clearAuth={mockClearAuth}
      />
    );

  const openMenu = async (): Promise<void> => {
    fireEvent.keyDown(screen.getByRole("combobox"), {
      key: "ArrowDown",
      keyCode: 40,
    });
    await screen.findByText("Other");
  };

  beforeEach(() => {
    mockFetch.mockResolvedValue({
      status: 200,
      json: async () => apiEvents.map((e) => ({ ...e })),
    });
    global.fetch = mockFetch;
  });

  afterEach(() => {
    jest.clearAllMocks();
    jest.useRealTimers();
  });

  it("loads the user's apiwrite events once and appends an Other option", async () => {
    renderSelector();
    await openMenu();

    expect(mockFetch).toHaveBeenCalledWith("/_/account/apiwrite_events", {
      credentials: "same-origin",
    });
    expect(screen.getByText("2025 SUNY Regional")).toBeInTheDocument();
    expect(screen.getByText("2025 Finger Lakes Regional")).toBeInTheDocument();
    expect(screen.getByText("Other")).toBeInTheDocument();
  });

  it("filters the cached events by the typed search text", async () => {
    renderSelector();
    await openMenu();
    const fetchCalls = mockFetch.mock.calls.length;

    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "finger" },
    });

    await screen.findByText("2025 Finger Lakes Regional");
    await waitFor(() => {
      expect(screen.queryByText("2025 SUNY Regional")).not.toBeInTheDocument();
    });
    expect(screen.queryByText("Other")).not.toBeInTheDocument();
    // The event list is cached at module level, so no further fetches happen.
    expect(mockFetch).toHaveBeenCalledTimes(fetchCalls);
  });

  it("selects a real event: clears auth, leaves manual mode and sets the key", async () => {
    renderSelector();
    await openMenu();

    fireEvent.click(screen.getByText("2025 SUNY Regional"));

    expect(mockClearAuth).toHaveBeenCalledTimes(1);
    expect(mockSetManualEvent).toHaveBeenCalledWith(false);
    expect(mockSetEvent).toHaveBeenCalledWith("2025nysu");
    await waitFor(() => {
      expect(screen.getByText("2025 SUNY Regional")).toBeInTheDocument();
    });
  });

  it("selects Other: clears auth, enters manual mode and blanks the key", async () => {
    renderSelector();
    await openMenu();

    fireEvent.click(screen.getByText("Other"));

    expect(mockClearAuth).toHaveBeenCalledTimes(1);
    expect(mockSetManualEvent).toHaveBeenCalledWith(true);
    expect(mockSetEvent).toHaveBeenCalledWith("");
  });

  it("debounces manual event key typing before calling setEvent", () => {
    jest.useFakeTimers();
    renderSelector(true);
    const input = screen.getByPlaceholderText("Event Key");

    fireEvent.change(input, { target: { value: "2025" } });
    fireEvent.change(input, { target: { value: "2025nysu" } });
    expect(mockSetEvent).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(499);
    });
    expect(mockSetEvent).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(mockSetEvent).toHaveBeenCalledTimes(1);
    expect(mockSetEvent).toHaveBeenCalledWith("2025nysu");
  });

  it("cancels a pending debounce when unmounted", () => {
    jest.useFakeTimers();
    const { unmount } = renderSelector(true);

    fireEvent.change(screen.getByPlaceholderText("Event Key"), {
      target: { value: "2025nysu" },
    });
    unmount();

    act(() => {
      jest.advanceTimersByTime(1000);
    });
    expect(mockSetEvent).not.toHaveBeenCalled();
  });
});
