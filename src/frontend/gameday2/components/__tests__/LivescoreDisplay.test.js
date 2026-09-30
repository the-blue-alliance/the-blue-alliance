/* @jest-environment jsdom */
import React from "react";
import { render, act } from "@testing-library/react";

// AutoScale measures the DOM, which jsdom cannot do; render its child directly.
jest.mock("../AutoScale/AutoScale", () => (props) => (
  <div data-testid="autoscale">{props.children}</div>
));
jest.mock("../CountWrapper", () => (props) => (
  <span data-testid="count">{props.number}</span>
));

import LivescoreDisplay from "../LivescoreDisplay";

const makeMatch = (shortKey, overrides = {}) => ({
  shortKey,
  c: "qm",
  m: Number(shortKey.replace(/\D/g, "")),
  s: 1,
  r: -1,
  b: -1,
  rt: ["frc254", "frc1678", "frc604"],
  bt: ["frc971", "frc846", "frc5940"],
  ...overrides,
});

const matches = [
  makeMatch("qm1", { r: 100, b: 50 }),
  makeMatch("qm2", { r: 80, b: 90 }),
  makeMatch("qm3"),
  makeMatch("qm4", { pt: 0 }),
];

const liveState = {
  mk: "qm2",
  m: "teleop",
  t: 100,
  rs: 55,
  rfc: 2,
  rfp: false,
  rlc: 1,
  rlp: true,
  rbc: 0,
  rbp: false,
  rswo: true,
  rsco: false,
  rcp: null,
  rpt: null,
  raq: true,
  rfb: false,
  bs: 40,
  bfc: 1,
  bfp: false,
  blc: 0,
  blp: false,
  bbc: 3,
  bbp: true,
  bswo: false,
  bsco: true,
  bcp: null,
  bpt: null,
  baq: false,
  bfb: true,
};

const renderDisplay = (matchState, extraMatches = matches) =>
  render(<LivescoreDisplay matches={extraMatches} matchState={matchState} />);

const ownership = (container) =>
  Array.from(container.querySelectorAll(".booleanIndicator")).map((el) => {
    if (el.classList.contains("red")) return "red";
    if (el.classList.contains("blue")) return "blue";
    return "none";
  });

describe("LivescoreDisplay", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("says live info is unavailable without a match state", () => {
    const { getByText } = renderDisplay(undefined);
    expect(getByText("Live match info not available")).toBeTruthy();
  });

  it("says live info is unavailable when the current match is unknown", () => {
    const { getByText } = renderDisplay({ ...liveState, mk: "qm99" });
    expect(getByText("Live match info not available")).toBeTruthy();
  });

  it("renders a live teleop match with scores, teams, ownership and powerups", () => {
    const { container, getByText, getAllByTestId } = renderDisplay(liveState);
    expect(getByText("Q2")).toBeTruthy();
    expect(getByText("100")).toBeTruthy();

    const counts = getAllByTestId("count").map((el) => el.textContent);
    expect(counts).toEqual(["55", "40"]);

    const red = container.querySelector(".redAlliance");
    expect(red.textContent).toBe("254167860455");
    const blue = container.querySelector(".blueAlliance");
    expect(blue.textContent).toBe("971846594040");

    // Owned indicators get the alliance color
    expect(ownership(container)).toEqual([
      "none", // red scale
      "red", // red switch
      "red", // red auto quest
      "none", // red face the boss
      "blue", // blue scale
      "none", // blue switch
      "none", // blue auto quest
      "blue", // blue face the boss
    ]);

    const powerups = container.querySelectorAll(".powerupCountContainer");
    expect(powerups).toHaveLength(6);
    expect(powerups[0].className).toContain("redCount2");
    expect(powerups[1].className).toContain("powerupCountContainerCenter");
    expect(powerups[1].className).toContain("red");
    expect(powerups[5].className).toContain("blueCount3");

    expect(container.querySelector(".currentPowerup")).toBeNull();

    const bar = container.querySelector(".progress-bar");
    expect(bar.className).toBe("progress-bar progress-bar-green");
    // (150 - 100) / 150
    expect(bar.style.width).toBe("33.333333333333336%");
  });

  it("colors every indicator when both alliances own everything", () => {
    const { container } = renderDisplay({
      ...liveState,
      rswo: true,
      rsco: true,
      raq: true,
      rfb: true,
      bswo: true,
      bsco: true,
      baq: true,
      bfb: true,
    });
    expect(
      Array.from(container.querySelectorAll(".booleanIndicator")).map(
        (el) => el.className
      )
    ).toEqual([
      "booleanIndicator red",
      "booleanIndicator red",
      "booleanIndicator red",
      "booleanIndicator red",
      "booleanIndicator blue",
      "booleanIndicator blue",
      "booleanIndicator blue",
      "booleanIndicator blue",
    ]);
  });

  it("shows the red alliance's active powerup", () => {
    const { container } = renderDisplay({
      ...liveState,
      rcp: "force",
      rpt: 7,
    });
    const powerup = container.querySelector(".currentPowerup");
    expect(powerup.className).toBe("currentPowerup red");
    expect(powerup.querySelector("img").getAttribute("src")).toBe(
      "/images/2018_force.png"
    );
    expect(powerup.textContent).toBe("7");
  });

  it("shows the blue alliance's active powerup", () => {
    const { container } = renderDisplay({
      ...liveState,
      bcp: "boost",
      bpt: 3,
    });
    const powerup = container.querySelector(".currentPowerup");
    expect(powerup.className).toBe("currentPowerup blue");
    expect(powerup.textContent).toBe("3");
  });

  it("turns the progress bar yellow in the last 30 seconds of teleop", () => {
    const { container } = renderDisplay({ ...liveState, t: 30 });
    expect(container.querySelector(".progress-bar").className).toBe(
      "progress-bar progress-bar-yellow"
    );
  });

  it("turns the progress bar red when teleop time runs out", () => {
    const { container } = renderDisplay({ ...liveState, t: 0 });
    const bar = container.querySelector(".progress-bar");
    expect(bar.className).toBe("progress-bar progress-bar-red");
    expect(bar.style.width).toBe("100%");
  });

  it("fills the first tenth of the bar during auto", () => {
    const { container } = renderDisplay({ ...liveState, m: "auto", t: 0 });
    const bar = container.querySelector(".progress-bar");
    expect(bar.className).toBe("progress-bar progress-bar-green");
    expect(bar.style.width).toBe("10%");
  });

  it("shows a full red bar after the match while scores are not yet posted", () => {
    // qm3 is still unplayed (r === -1), so post_match keeps showing it
    const { container, getByText } = renderDisplay({
      ...liveState,
      mk: "qm3",
      m: "post_match",
    });
    expect(getByText("Q3")).toBeTruthy();
    const bar = container.querySelector(".progress-bar");
    expect(bar.className).toBe("progress-bar progress-bar-red");
    expect(bar.style.width).toBe("100%");
  });

  it("advances to the next unplayed match with an ETA once the current one is scored", () => {
    // Current time is 10 minutes before qm3's predicted time
    const now = 1_700_000_000;
    jest.setSystemTime(now * 1000);
    const withTimes = [
      makeMatch("qm1", { r: 100, b: 50 }),
      makeMatch("qm2", { r: 80, b: 90 }),
      makeMatch("qm3", { pt: now + 600 }),
    ];
    const { container, getByText } = renderDisplay(
      { ...liveState, mk: "qm2", m: "post_match" },
      withTimes
    );
    expect(getByText("Q3 in ~10 min")).toBeTruthy();
    // Everything resets to pre-match defaults
    const bar = container.querySelector(".progress-bar");
    expect(bar.className).toBe("progress-bar progress-bar-green");
    expect(bar.style.width).toBe("0%");
    expect(container.querySelector(".timeRemaining").textContent).toBe("0");
    expect(ownership(container)).toEqual(Array(8).fill("none"));
  });

  it("formats the ETA as <2 min, minutes, or hours", () => {
    const now = 1_700_000_000;
    jest.setSystemTime(now * 1000);
    const at = (seconds) => [makeMatch("qm1", { pt: now + seconds })];
    const state = { ...liveState, mk: "qm1", m: "pre_match" };

    expect(renderDisplay(state, at(60)).getByText("Q1 in <2 min")).toBeTruthy();
    expect(
      renderDisplay(state, at(45 * 60)).getByText("Q1 in ~45 min")
    ).toBeTruthy();
    expect(
      renderDisplay(state, at(3 * 3600)).getByText("Q1 in ~3 h")
    ).toBeTruthy();
  });

  it("says the match is next when it has no predicted time", () => {
    const { getByText } = renderDisplay({
      ...liveState,
      mk: "qm3",
      m: "pre_match",
    });
    expect(getByText("Q3 is next")).toBeTruthy();
  });

  it("says the match is next when there is no predicted time (pt of 0 is falsy)", () => {
    const { getByText } = renderDisplay({
      ...liveState,
      mk: "qm4",
      m: "pre_match",
    });
    expect(getByText("Q4 is next")).toBeTruthy();
  });

  it("says the next match is next when the clock has not ticked yet", () => {
    // Before componentDidMount's first tick, currentTime is undefined
    const spy = jest
      .spyOn(LivescoreDisplay.prototype, "componentDidMount")
      .mockImplementation(() => {});
    const { getByText } = renderDisplay(
      { ...liveState, mk: "qm1", m: "pre_match" },
      [makeMatch("qm1", { pt: 1_700_000_600 })]
    );
    expect(getByText("Q1 is next")).toBeTruthy();
    spy.mockRestore();
  });

  it("labels playoff matches with their set number", () => {
    const { getByText } = renderDisplay({ ...liveState, mk: "sf2" }, [
      makeMatch("sf2", { c: "sf", s: 2, m: 1 }),
    ]);
    expect(getByText("SF2-1")).toBeTruthy();
  });

  it("refreshes the clock every ten seconds", () => {
    const setIntervalSpy = jest.spyOn(global, "setInterval");
    const now = 1_700_000_000;
    jest.setSystemTime(now * 1000);
    const { getByText, unmount } = renderDisplay(
      { ...liveState, mk: "qm1", m: "pre_match" },
      [makeMatch("qm1", { pt: now + 30 * 60 })]
    );
    expect(getByText("Q1 in ~30 min")).toBeTruthy();
    expect(setIntervalSpy).toHaveBeenCalledWith(expect.any(Function), 10000);

    act(() => {
      jest.setSystemTime((now + 20 * 60) * 1000);
      jest.advanceTimersByTime(10000);
    });
    expect(getByText("Q1 in ~10 min")).toBeTruthy();

    unmount();
    setIntervalSpy.mockRestore();
  });

  it("Bug #36: clears its refresh interval on unmount", () => {
    // Wrong today: componentDidMount starts a 10s setInterval that is never
    // cleared, so it keeps calling setState after the component is gone.
    // Correct: componentWillUnmount clears the interval it started.
    const setIntervalSpy = jest.spyOn(global, "setInterval");
    const clearIntervalSpy = jest.spyOn(global, "clearInterval");
    try {
      const { unmount } = renderDisplay(liveState);
      const call = setIntervalSpy.mock.calls.findIndex(
        ([, ms]) => ms === 10000
      );
      expect(call).not.toBe(-1);
      const intervalId = setIntervalSpy.mock.results[call].value;
      unmount();
      expect(clearIntervalSpy).toHaveBeenCalledWith(intervalId);
    } finally {
      setIntervalSpy.mockRestore();
      clearIntervalSpy.mockRestore();
    }
  });

  it("Bug #36: validates the matches prop with a real PropTypes validator", () => {
    // Wrong today: propTypes declares `matches: PropTypes.list`, which does
    // not exist, so the validator is undefined and the prop is unchecked.
    // Correct: a real validator such as PropTypes.array / arrayOf(...).
    expect(typeof LivescoreDisplay.propTypes.matches).toBe("function");
  });

  it("Bug #36: never leaks false or 0 into the indicator class names", () => {
    // Wrong today: class names are built with `${x && "red"}`, so unowned
    // indicators render as "booleanIndicator false", and after the pre-match
    // reset (0 for red switch/scale) as "booleanIndicator 0".
    // Correct: unowned indicators are just "booleanIndicator".
    const now = 1_700_000_000;
    jest.setSystemTime(now * 1000);
    const live = renderDisplay(liveState);
    const reset = renderDisplay({ ...liveState, mk: "qm2", m: "post_match" }, [
      makeMatch("qm1", { r: 100, b: 50 }),
      makeMatch("qm2", { r: 80, b: 90 }),
      makeMatch("qm3", { pt: now + 600 }),
    ]);
    [live.container, reset.container].forEach((container) => {
      container.querySelectorAll(".booleanIndicator").forEach((el) => {
        expect(Array.from(el.classList)).not.toContain("false");
        expect(Array.from(el.classList)).not.toContain("0");
      });
    });
  });
});
