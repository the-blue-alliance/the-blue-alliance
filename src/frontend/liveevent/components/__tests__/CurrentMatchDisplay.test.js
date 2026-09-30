/* @jest-environment jsdom */

import React from "react";
import { render, screen } from "@testing-library/react";
import CurrentMatchDisplay from "../CurrentMatchDisplay";

jest.mock("../../../gameday2/components/CountWrapper", () => (props) => (
  <span className="count">{props.number}</span>
));

const match = {
  key: "2018casj_qm3",
  c: "qm",
  s: 1,
  m: 3,
  rt: ["frc254", "frc604", "frc1678"],
  bt: ["frc971", "frc973", "frc1323"],
};

const liveState = {
  m: "teleop",
  t: 100,
  rs: 120,
  rfc: 3,
  rfp: true,
  rlc: 2,
  rlp: false,
  rbc: 1,
  rbp: true,
  rswo: true,
  rsco: true,
  rcp: null,
  rpt: null,
  raq: true,
  rfb: true,
  bs: 80,
  bfc: 0,
  bfp: false,
  blc: 1,
  blp: false,
  bbc: 2,
  bbp: false,
  bswo: false,
  bsco: false,
  bcp: "boost",
  bpt: 7,
  baq: false,
  bfb: false,
};

const renderDisplay = (matchState, forcePreMatch = false) =>
  render(
    <CurrentMatchDisplay
      year={2018}
      match={match}
      matchState={matchState}
      forcePreMatch={forcePreMatch}
    />
  ).container;

const progressBar = (container) => container.querySelector(".progress-bar");

describe("CurrentMatchDisplay", () => {
  it("shows a spinner when there is no match", () => {
    const { container } = render(
      <CurrentMatchDisplay year={2018} match={null} matchState={null} />
    );
    expect(container.querySelector(".glyphicon-refresh")).not.toBeNull();
  });

  it("shows a message when there is no live match state", () => {
    render(<CurrentMatchDisplay year={2018} match={match} matchState={null} />);
    expect(screen.getByText("Live match info not available")).toBeTruthy();
  });

  it("renders the live teleop state", () => {
    const container = renderDisplay(liveState);
    expect(progressBar(container).className).toBe(
      "progress-bar progress-bar-success"
    );
    expect(progressBar(container).style.width).toBe(`${(50 * 100) / 150}%`);
    expect(container.querySelector(".timeRemaining").textContent).toBe("100");
    expect(container.querySelector(".score.red").textContent).toBe("120");
    expect(container.querySelector(".score.blue").textContent).toBe("80");
    expect(
      container.querySelector('.redAlliance a[href="/team/254/2018"]')
    ).not.toBeNull();
    expect(
      container.querySelector('.blueAlliance a[href="/team/1323/2018"]')
    ).not.toBeNull();
    expect(container.querySelectorAll(".booleanIndicator.red")).toHaveLength(4);
    // Pins current behavior: falsy indicator values are interpolated into
    // the class name (e.g. "booleanIndicator false").
    expect(container.querySelectorAll(".booleanIndicator.false")).toHaveLength(
      4
    );
    const powerup = container.querySelector(".currentPowerup");
    expect(powerup.className).toBe("currentPowerup blue");
    expect(powerup.querySelector("img").getAttribute("src")).toBe(
      "/images/2018_boost.png"
    );
    expect(powerup.textContent).toBe("7");
  });

  it("shows the red powerup when red has one active", () => {
    const container = renderDisplay(
      Object.assign({}, liveState, { rcp: "force", rpt: 5 })
    );
    const powerup = container.querySelector(".currentPowerup");
    expect(powerup.className).toBe("currentPowerup red");
    expect(powerup.textContent).toBe("5");
  });

  it("warns during the last 30 seconds of teleop", () => {
    const container = renderDisplay(Object.assign({}, liveState, { t: 30 }));
    expect(progressBar(container).className).toBe(
      "progress-bar progress-bar-warning"
    );
  });

  it("shows danger when teleop time has run out", () => {
    const container = renderDisplay(Object.assign({}, liveState, { t: 0 }));
    expect(progressBar(container).className).toBe(
      "progress-bar progress-bar-danger"
    );
    expect(progressBar(container).style.width).toBe("100%");
  });

  it("fills the bar after the match", () => {
    const container = renderDisplay(
      Object.assign({}, liveState, { m: "post_match", t: 0 })
    );
    expect(progressBar(container).className).toBe(
      "progress-bar progress-bar-danger"
    );
    expect(progressBar(container).style.width).toBe("100%");
  });

  it("scales auto progress against the full match length", () => {
    const container = renderDisplay(
      Object.assign({}, liveState, { m: "auto", t: 5 })
    );
    expect(progressBar(container).className).toBe(
      "progress-bar progress-bar-success"
    );
    expect(progressBar(container).style.width).toBe(`${(10 * 100) / 150}%`);
  });

  it("resets everything to a blank pre-match display when forced", () => {
    const container = renderDisplay(liveState, true);
    expect(progressBar(container).style.width).toBe("0%");
    expect(container.querySelector(".timeRemaining").textContent).toBe("0");
    expect(container.querySelector(".score.red").textContent).toBe("0");
    expect(container.querySelector(".score.blue").textContent).toBe("0");
    expect(container.querySelector(".currentPowerup")).toBeNull();
    expect(container.querySelectorAll(".powerCubeActive")).toHaveLength(0);
    expect(container.querySelectorAll(".booleanIndicator.red")).toHaveLength(0);
  });
});
