import { getScheduledStartTimeLabel } from "../WebcastSelectionDialog";

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
