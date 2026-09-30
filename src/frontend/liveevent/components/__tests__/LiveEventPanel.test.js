/* @jest-environment jsdom */

import React from "react";
import { act, render } from "@testing-library/react";
import LiveEventPanel from "../LiveEventPanel";

const mockListeners = {};
jest.mock("../../firebaseapp", () => ({
  __esModule: true,
  default: {
    database: () => ({
      ref: (path) => ({
        on: (event, cb) => {
          mockListeners[path] = cb;
        },
      }),
    }),
  },
}));
jest.mock("../CurrentMatchDisplay", () => (props) => (
  <div
    data-testid="current-match"
    data-match={props.match.shortKey}
    data-force-pre-match={String(props.forcePreMatch)}
  />
));
jest.mock("../LastMatchesTable", () => (props) => (
  <div data-testid="last-matches">
    {props.matches === null
      ? "loading"
      : props.matches.map((m) => m.shortKey).join(",")}
  </div>
));
jest.mock("../UpcomingMatchesTable", () => (props) => (
  <div data-testid="upcoming-matches">
    {props.matches === null
      ? "loading"
      : props.matches.map((m) => m.shortKey).join(",")}
  </div>
));

const NOW = 1700000000; // seconds

const qm = (m, played, extra) =>
  Object.assign(
    { c: "qm", s: 1, m, r: played ? 10 : -1, b: played ? 20 : -1 },
    extra
  );

const matches = () => ({
  qm1: qm(1, false), // Skipped: unplayed but followed by played matches
  qm2: qm(2, true),
  qm3: qm(3, true),
  qm4: qm(4, false, { pt: NOW + 60 }),
  qm5: qm(5, false),
  qm6: qm(6, false),
  qm7: qm(7, false),
  bad: { c: "zz", r: 1, b: 2 }, // Unknown comp level sorts first
});

const text = (container, id) =>
  container.querySelector(`[data-testid="${id}"]`).textContent;

const setUp = (props = {}) => {
  const utils = render(
    <LiveEventPanel eventKey="2018casj" simple={false} {...props} />
  );
  const push = (path, val) =>
    act(() => {
      mockListeners[path]({ val: () => val });
    });
  return { ...utils, push };
};

describe("LiveEventPanel", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(NOW * 1000);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("shows loading tables before any data arrives", () => {
    const { container } = setUp();
    expect(text(container, "last-matches")).toBe("loading");
    expect(text(container, "upcoming-matches")).toBe("loading");
    expect(container.querySelector('[data-testid="current-match"]')).toBeNull();
    expect(container.querySelectorAll(".col-lg-6")).toHaveLength(2);
  });

  it("handles an event with no matches", () => {
    const { container, push } = setUp();
    push("/e/2018casj/m", null);
    push("/le/2018casj", null);
    expect(text(container, "last-matches")).toBe("");
    expect(text(container, "upcoming-matches")).toBe("");
  });

  it("lists played and upcoming matches when there is no live state", () => {
    const { container, push } = setUp();
    push("/e/2018casj/m", matches());
    expect(text(container, "last-matches")).toBe("bad,qm2,qm3");
    expect(text(container, "upcoming-matches")).toBe("qm4,qm5,qm6");
    expect(container.querySelector('[data-testid="current-match"]')).toBeNull();
  });

  it("ignores pre-match live states", () => {
    const { container, push } = setUp();
    push("/e/2018casj/m", matches());
    push("/le/2018casj", { mk: "pm1", m: "pre_match" });
    expect(text(container, "upcoming-matches")).toBe("qm4,qm5,qm6");
    expect(container.querySelector('[data-testid="current-match"]')).toBeNull();
  });

  it("shows an unplayed match that is in progress as the current match", () => {
    const { container, push } = setUp();
    push("/e/2018casj/m", matches());
    push("/le/2018casj", { mk: "qm4", m: "teleop" });
    expect(container.textContent).toContain("Current Match: Quals 4");
    const current = container.querySelector('[data-testid="current-match"]');
    expect(current.getAttribute("data-match")).toBe("qm4");
    expect(current.getAttribute("data-force-pre-match")).toBe("false");
    expect(text(container, "upcoming-matches")).toBe("qm5,qm6,qm7");
    expect(container.querySelectorAll(".col-lg-3")).toHaveLength(2);
  });

  it("shows a played match whose results are posted but still in progress", () => {
    const { container, push } = setUp();
    push("/e/2018casj/m", matches());
    push("/le/2018casj", { mk: "qm3", m: "teleop" });
    expect(text(container, "last-matches")).toBe("bad,qm2");
    expect(
      container
        .querySelector('[data-testid="current-match"]')
        .getAttribute("data-match")
    ).toBe("qm3");
  });

  it("shows the next match with an ETA after the current match ends", () => {
    const { container, push } = setUp();
    push("/e/2018casj/m", matches());
    push("/le/2018casj", { mk: "qm3", m: "post_match" });
    expect(text(container, "last-matches")).toBe("bad,qm2,qm3");
    expect(container.textContent).toContain("Next Match in <2 min: Quals 4");
    expect(
      container
        .querySelector('[data-testid="current-match"]')
        .getAttribute("data-force-pre-match")
    ).toBe("true");
    expect(text(container, "upcoming-matches")).toBe("qm5,qm6,qm7");
  });

  it.each([
    [30 * 60, " in ~30 min"],
    [3 * 60 * 60, " in ~3 h"],
  ])("formats a next match ETA %i seconds away", (delta, eta) => {
    const { container, push } = setUp();
    const data = matches();
    data.qm4.pt = NOW + delta;
    push("/e/2018casj/m", data);
    push("/le/2018casj", { mk: "qm3", m: "post_match" });
    expect(container.textContent).toContain(`Next Match${eta}: Quals 4`);
  });

  it("omits the ETA when the next match has no scheduled time", () => {
    const { container, push } = setUp();
    const data = matches();
    delete data.qm4.pt;
    push("/e/2018casj/m", data);
    push("/le/2018casj", { mk: "qm3", m: "post_match" });
    expect(container.textContent).toContain("Next Match: Quals 4");
  });

  it("refreshes the current time every 10 seconds", () => {
    const { container, push } = setUp();
    const data = matches();
    data.qm4.pt = NOW + 30 * 60;
    push("/e/2018casj/m", data);
    push("/le/2018casj", { mk: "qm3", m: "post_match" });
    expect(container.textContent).toContain("Next Match in ~30 min");
    act(() => {
      jest.setSystemTime((NOW + 29 * 60) * 1000);
      jest.advanceTimersByTime(10000);
    });
    expect(container.textContent).toContain("Next Match in <2 min");
  });

  it("shows nothing current once every match has been played", () => {
    const { container, push } = setUp();
    push("/e/2018casj/m", { qm1: qm(1, true) });
    push("/le/2018casj", { mk: "qm1", m: "post_match" });
    expect(container.querySelector('[data-testid="current-match"]')).toBeNull();
    expect(text(container, "upcoming-matches")).toBe("");
  });

  it("renders only the current match in simple mode", () => {
    const { container, push } = setUp({ simple: true });
    expect(container.querySelector('[data-testid="last-matches"]')).toBeNull();
    expect(
      container.querySelector('[data-testid="upcoming-matches"]')
    ).toBeNull();
    push("/e/2018casj/m", matches());
    push("/le/2018casj", { mk: "qm4", m: "auto" });
    expect(
      container.querySelector('[data-testid="current-match"]').parentElement
        .className
    ).toBe(" text-center livePanelColumn");
  });
});
