/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";

jest.mock("react-ga4", () => ({
  __esModule: true,
  default: { event: jest.fn() },
}));

import ReactGA from "react-ga4";
import ChatAnalyticsTracker from "../ChatAnalyticsTracker";
import LayoutAnalyticsTracker from "../LayoutAnalyticsTracker";
import VideoCellAnalyticsTracker from "../VideoCellAnalyticsTracker";

const ONE_MINUTE = 60000;

beforeEach(() => {
  jest.useFakeTimers();
  ReactGA.event.mockClear();
});

afterEach(() => {
  jest.useRealTimers();
});

describe("ChatAnalyticsTracker", () => {
  it("reports the selected chat on mount and every minute thereafter", () => {
    const { container, unmount } = render(
      <ChatAnalyticsTracker currentChat="firstinspires" />
    );
    expect(container.innerHTML).toBe("");
    expect(ReactGA.event).toHaveBeenCalledTimes(1);
    expect(ReactGA.event).toHaveBeenLastCalledWith({
      category: "Selected Chat Time",
      action: "firstinspires",
      label: "0",
      value: 0,
    });

    jest.advanceTimersByTime(ONE_MINUTE);
    expect(ReactGA.event).toHaveBeenCalledTimes(2);
    expect(ReactGA.event).toHaveBeenLastCalledWith({
      category: "Selected Chat Time",
      action: "firstinspires",
      label: "1",
      value: 1,
    });

    jest.advanceTimersByTime(ONE_MINUTE);
    expect(ReactGA.event).toHaveBeenLastCalledWith(
      expect.objectContaining({ label: "2", value: 1 })
    );

    unmount();
    jest.advanceTimersByTime(5 * ONE_MINUTE);
    expect(ReactGA.event).toHaveBeenCalledTimes(3);
  });

  it("restarts the clock when the chat changes", () => {
    const { rerender } = render(
      <ChatAnalyticsTracker currentChat="firstinspires" />
    );
    jest.advanceTimersByTime(ONE_MINUTE);
    expect(ReactGA.event).toHaveBeenCalledTimes(2);

    rerender(<ChatAnalyticsTracker currentChat="firstupdatesnow" />);
    expect(ReactGA.event).toHaveBeenCalledTimes(3);
    expect(ReactGA.event).toHaveBeenLastCalledWith({
      category: "Selected Chat Time",
      action: "firstupdatesnow",
      label: "0",
      value: 0,
    });

    // The old interval was cleared: only one event per minute is sent
    jest.advanceTimersByTime(ONE_MINUTE);
    expect(ReactGA.event).toHaveBeenCalledTimes(4);
    expect(ReactGA.event).toHaveBeenLastCalledWith(
      expect.objectContaining({ action: "firstupdatesnow", label: "1" })
    );
  });

  it("does not restart when re-rendered with the same chat", () => {
    const { rerender } = render(
      <ChatAnalyticsTracker currentChat="firstinspires" />
    );
    rerender(<ChatAnalyticsTracker currentChat="firstinspires" />);
    expect(ReactGA.event).toHaveBeenCalledTimes(1);
  });
});

describe("LayoutAnalyticsTracker", () => {
  it("reports the layout name on mount and every minute thereafter", () => {
    const { unmount } = render(<LayoutAnalyticsTracker layoutId={3} />);
    expect(ReactGA.event).toHaveBeenCalledWith({
      category: "Selected Layout Time",
      action: "Quad View",
      label: "0",
      value: 0,
    });

    jest.advanceTimersByTime(ONE_MINUTE);
    expect(ReactGA.event).toHaveBeenLastCalledWith({
      category: "Selected Layout Time",
      action: "Quad View",
      label: "1",
      value: 1,
    });

    unmount();
    jest.advanceTimersByTime(5 * ONE_MINUTE);
    expect(ReactGA.event).toHaveBeenCalledTimes(2);
  });

  it("restarts the clock when the layout changes", () => {
    const { rerender } = render(<LayoutAnalyticsTracker layoutId={0} />);
    jest.advanceTimersByTime(ONE_MINUTE);
    rerender(<LayoutAnalyticsTracker layoutId={0} />);
    expect(ReactGA.event).toHaveBeenCalledTimes(2);

    rerender(<LayoutAnalyticsTracker layoutId={1} />);
    expect(ReactGA.event).toHaveBeenCalledTimes(3);
    expect(ReactGA.event).toHaveBeenLastCalledWith({
      category: "Selected Layout Time",
      action: "Vertical Split View",
      label: "0",
      value: 0,
    });

    jest.advanceTimersByTime(ONE_MINUTE);
    expect(ReactGA.event).toHaveBeenCalledTimes(4);
  });
});

describe("VideoCellAnalyticsTracker", () => {
  const webcast = {
    key: "2026casj",
    num: 0,
    id: "2026CASJ-0",
    name: "Silicon Valley Regional",
    type: "Twitch",
    channel: "FIRSTinspires",
  };

  it("reports the lowercased webcast identity on mount and every minute", () => {
    const { container, unmount } = render(
      <VideoCellAnalyticsTracker webcast={webcast} />
    );
    expect(container.innerHTML).toBe("");
    expect(ReactGA.event).toHaveBeenCalledWith({
      category: "Webcast View Time",
      action: "2026casj-0::twitch::firstinspires",
      label: "0",
      value: 0,
    });

    jest.advanceTimersByTime(ONE_MINUTE);
    expect(ReactGA.event).toHaveBeenLastCalledWith(
      expect.objectContaining({ label: "1", value: 1 })
    );

    unmount();
    jest.advanceTimersByTime(5 * ONE_MINUTE);
    expect(ReactGA.event).toHaveBeenCalledTimes(2);
  });

  it("includes the file for webcasts that have one", () => {
    render(<VideoCellAnalyticsTracker webcast={{ ...webcast, file: "Ev1" }} />);
    expect(ReactGA.event).toHaveBeenCalledWith(
      expect.objectContaining({
        action: "2026casj-0::twitch::firstinspires::ev1",
      })
    );
  });
});
