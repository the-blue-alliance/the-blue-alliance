/* @jest-environment jsdom */
import React from "react";
import { render, fireEvent } from "@testing-library/react";
import WebcastSelectionDialog, {
  getScheduledStartTimeLabel,
} from "../WebcastSelectionDialog";

describe("getScheduledStartTimeLabel", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("returns null when no scheduled start time exists", () => {
    expect(getScheduledStartTimeLabel(null)).toBeNull();
  });

  it("returns null when scheduled start time is invalid", () => {
    expect(getScheduledStartTimeLabel("not-a-time")).toBeNull();
  });

  it("formats scheduled start time as local time with a timer icon", () => {
    const localTimeSpy = jest
      .spyOn(Date.prototype, "toLocaleTimeString")
      .mockReturnValue("11:30 AM");

    expect(getScheduledStartTimeLabel("2026-03-14T15:30:00Z")).toEqual(
      "⏲\n11:30 AM"
    );
    expect(localTimeSpy).toHaveBeenCalledWith([], {
      hour: "numeric",
      minute: "2-digit",
    });
  });
});

const makeWebcast = (id, overrides = {}) => ({
  key: id.split("-")[0],
  num: 0,
  id,
  name: `Webcast ${id}`,
  type: "twitch",
  channel: id,
  ...overrides,
});

const webcastsById = {
  "2026casj-0": makeWebcast("2026casj-0", {
    status: "online",
    viewerCount: 1234,
    streamTitle: "Qualification 12",
    type: "youtube",
  }),
  "2026nyro-0": makeWebcast("2026nyro-0", { status: "online" }),
  "2026txho-0": makeWebcast("2026txho-0", {
    status: "offline",
    scheduledStartTimeUtc: "2026-03-14T15:30:00Z",
  }),
  "2026miket-0": makeWebcast("2026miket-0", {
    status: "offline",
    scheduled_start_time_utc: "2026-03-14T16:30:00Z",
  }),
  "2026waahs-0": makeWebcast("2026waahs-0", { status: "offline" }),
  "2026unknown-0": makeWebcast("2026unknown-0"),
  "firstupdatesnow-0": makeWebcast("firstupdatesnow-0", { status: "online" }),
  "firstinspires-0": makeWebcast("firstinspires-0", { status: "offline" }),
  "bluezone-0": makeWebcast("bluezone-0", { name: "BlueZone" }),
};

const renderDialog = (props = {}) => {
  const allProps = {
    open: true,
    webcasts: Object.keys(webcastsById),
    webcastsById,
    specialWebcastIds: new Set(["firstupdatesnow-0", "firstinspires-0"]),
    displayedWebcasts: [],
    onWebcastSelected: jest.fn(),
    onRequestClose: jest.fn(),
    ...props,
  };
  const utils = render(<WebcastSelectionDialog {...allProps} />);
  return { ...utils, props: allProps };
};

// Flattens the dialog's list into headers, item names and "---" dividers so
// tests can assert on the grouping and ordering in one go.
const listText = () =>
  Array.from(document.querySelectorAll(".MuiList-root > *")).map((el) => {
    if (el.classList.contains("MuiDivider-root")) {
      return "---";
    }
    const primary = el.querySelector(".MuiListItemText-primary");
    return primary ? primary.textContent : el.textContent;
  });

describe("WebcastSelectionDialog", () => {
  beforeEach(() => {
    jest
      .spyOn(Date.prototype, "toLocaleTimeString")
      .mockReturnValue("11:30 AM");
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("groups webcasts into special, event, offline event and offline special sections", () => {
    const { getByText } = renderDialog();
    expect(getByText("Select a webcast")).toBeTruthy();
    expect(listText()).toEqual([
      "Special Webcasts",
      "BlueZone",
      "Webcast firstupdatesnow-0",
      "---",
      "Event Webcasts",
      "Webcast 2026casj-0",
      "Webcast 2026nyro-0",
      "Webcast 2026unknown-0",
      "---",
      "Offline Event Webcasts",
      "Webcast 2026txho-0",
      "Webcast 2026miket-0",
      "Webcast 2026waahs-0",
      "---",
      "Offline Special Webcasts",
      "Webcast firstinspires-0",
    ]);
  });

  it("shows platform, viewer count, stream title and status for online webcasts", () => {
    const { getByText } = renderDialog();
    const item = getByText("Webcast 2026casj-0").closest("li");
    expect(
      item.querySelector(".MuiListItemIcon-root svg").getAttribute("viewBox")
    ).toBe("0 0 576 512");
    expect(item.textContent).toContain("1,234");
    expect(item.textContent).toContain("Viewers");
    expect(item.querySelector(".MuiListItemText-secondary").textContent).toBe(
      "Qualification 12"
    );
    expect(item.querySelector('[data-testid="VideocamIcon"]').style.color).toBe(
      "rgb(76, 175, 80)"
    );

    const noViewers = getByText("Webcast 2026nyro-0").closest("li");
    expect(noViewers.textContent).not.toContain("Viewers");
    expect(noViewers.querySelector(".MuiListItemText-secondary")).toBeNull();
    expect(
      noViewers.querySelector('[data-testid="VideocamIcon"]')
    ).not.toBeNull();
  });

  it("shows the scheduled start time for offline webcasts that have one, from either field spelling", () => {
    const { getByText } = renderDialog();
    const camel = getByText("Webcast 2026txho-0").closest("li");
    expect(camel.textContent).toContain("⏲\n11:30 AM");
    expect(camel.querySelector('[data-testid="VideocamOffIcon"]')).toBeNull();

    const snake = getByText("Webcast 2026miket-0").closest("li");
    expect(snake.textContent).toContain("⏲\n11:30 AM");

    const unscheduled = getByText("Webcast 2026waahs-0").closest("li");
    expect(
      unscheduled.querySelector('[data-testid="VideocamOffIcon"]')
    ).not.toBeNull();
  });

  it("shows a help icon for webcasts with unknown status", () => {
    const { getByText } = renderDialog();
    const item = getByText("Webcast 2026unknown-0").closest("li");
    expect(item.querySelector('[data-testid="HelpIcon"]')).not.toBeNull();
  });

  it("describes and stars the BlueZone webcast", () => {
    const { getByText } = renderDialog();
    const item = getByText("BlueZone").closest("li");
    expect(item.querySelector(".MuiListItemText-secondary").textContent).toBe(
      "The best matches from across FRC"
    );
    expect(item.querySelector('[data-testid="GradeIcon"]')).not.toBeNull();
  });

  it("omits webcasts that are already displayed", () => {
    const { queryByText } = renderDialog({
      displayedWebcasts: ["2026casj-0", "bluezone-0"],
    });
    expect(queryByText("Webcast 2026casj-0")).toBeNull();
    expect(queryByText("BlueZone")).toBeNull();
  });

  it("only separates sections that are both present", () => {
    const { queryByText } = renderDialog({
      webcasts: ["2026casj-0", "2026txho-0", "firstinspires-0"],
    });
    expect(queryByText("Special Webcasts")).toBeNull();
    expect(listText()).toEqual([
      "Event Webcasts",
      "Webcast 2026casj-0",
      "---",
      "Offline Event Webcasts",
      "Webcast 2026txho-0",
      "---",
      "Offline Special Webcasts",
      "Webcast firstinspires-0",
    ]);
  });

  it("lists offline event webcasts without a divider when no event webcasts are online", () => {
    renderDialog({ webcasts: ["2026txho-0", "2026waahs-0"] });
    expect(listText()).toEqual([
      "Offline Event Webcasts",
      "Webcast 2026txho-0",
      "Webcast 2026waahs-0",
    ]);
  });

  it("uses no dividers when the neighbouring sections are absent", () => {
    renderDialog({ webcasts: ["firstinspires-0"] });
    expect(listText()).toEqual([
      "Offline Special Webcasts",
      "Webcast firstinspires-0",
    ]);
  });

  it("treats every webcast as a regular one when specialWebcastIds is not a Set", () => {
    renderDialog({
      webcasts: ["firstupdatesnow-0"],
      specialWebcastIds: ["firstupdatesnow-0"],
    });
    expect(listText()).toEqual(["Event Webcasts", "Webcast firstupdatesnow-0"]);
  });

  it("says so when no webcasts remain", () => {
    const { getByText } = renderDialog({ webcasts: [] });
    expect(getByText("No more webcasts available")).toBeTruthy();
  });

  it("reports the chosen webcast", () => {
    const { getByText, props } = renderDialog();
    fireEvent.click(getByText("Webcast 2026nyro-0"));
    expect(props.onWebcastSelected).toHaveBeenCalledWith("2026nyro-0");
  });

  it("closes from the cancel button and the backdrop", () => {
    const { getByText, props } = renderDialog();
    fireEvent.click(getByText("Cancel"));
    expect(props.onRequestClose).toHaveBeenCalledTimes(1);
    fireEvent.click(document.querySelector(".MuiBackdrop-root"));
    expect(props.onRequestClose).toHaveBeenCalledTimes(2);
  });

  it("tolerates a missing onRequestClose", () => {
    const { getByText } = renderDialog({ onRequestClose: undefined });
    expect(() => fireEvent.click(getByText("Cancel"))).not.toThrow();
  });

  it("renders nothing while closed", () => {
    const { queryByText } = renderDialog({ open: false });
    expect(queryByText("Select a webcast")).toBeNull();
  });
});
