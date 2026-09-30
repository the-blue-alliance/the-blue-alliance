/* @jest-environment jsdom */

import React from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import TrajectoryVisualizer from "../TrajectoryVisualizer";

jest.mock("../RobotTrajectory", () => (props) => (
  <g
    data-testid="trajectory"
    data-team={props.teamData.team_key}
    data-color={props.color}
    data-start={props.startTime}
    data-end={props.endTime}
    data-indicator-at-start={String(props.indicatorAtStart)}
  />
));

const team = (key) => ({ team_key: key, xs: [], ys: [] });
const data = {
  times: new Array(1500).fill(0),
  alliances: {
    red: [team("frc1"), team("frc2"), team("frc3")],
    blue: [team("frc4"), team("frc5"), team("frc6")],
  },
};

const trajectories = () => screen.getAllByTestId("trajectory");
const clock = (container) =>
  container.querySelector('input[type="range"]').nextSibling.textContent;
const button = (container, icon) =>
  container.querySelector(`.glyphicon-${icon}`).parentElement;
// requestAnimationFrame fires on ~16ms ticks under fake timers, so playback
// progress is checked within a frame or two of the ideal value.
const expectNear = (value, expected, tolerance) => {
  expect(Math.abs(Number(value) - expected)).toBeLessThanOrEqual(tolerance);
};
const step = (ms) =>
  act(() => {
    jest.advanceTimersByTime(ms);
  });

describe("TrajectoryVisualizer", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("shows the whole match for all six robots by default", () => {
    const { container } = render(
      <TrajectoryVisualizer fieldImg="/images/2019_field.png" data={data} />
    );
    expect(
      trajectories().map((t) => [t.dataset.team, t.dataset.color])
    ).toEqual([
      ["frc1", "#FF0000"],
      ["frc2", "#800000"],
      ["frc3", "#FF8080"],
      ["frc4", "#0000FF"],
      ["frc5", "#000080"],
      ["frc6", "#8080FF"],
    ]);
    trajectories().forEach((t) => {
      expect(t.dataset.start).toBe("0");
      expect(t.dataset.end).toBe("1500");
      expect(t.dataset.indicatorAtStart).toBe("true");
    });
    expect(button(container, "eye-open").disabled).toBe(true);
    expect(clock(container)).toBe("00:00");
    expect(screen.getByText("5x")).toBeTruthy();
  });

  it("plays back the match, wrapping around at the end", () => {
    const { container } = render(
      <TrajectoryVisualizer fieldImg="/f.png" data={data} />
    );
    fireEvent.click(button(container, "play"));
    expect(button(container, "pause")).toBeTruthy();
    expect(button(container, "eye-open").disabled).toBe(false);

    // 5x speed: 1 second of wall time is 50 samples (5 seconds of match)
    step(1000);
    const t = trajectories()[0];
    expectNear(t.dataset.end, 50, 2);
    expect(t.dataset.start).toBe("0");
    expect(t.dataset.indicatorAtStart).toBe("false");
    expect(clock(container)).toMatch(/^00:0[45]$/);

    step(1000);
    expectNear(trajectories()[0].dataset.start, 50, 4);

    // 29 more seconds wraps past the 150 second match
    step(29000);
    expect(Number(trajectories()[0].dataset.end)).toBeLessThan(100);

    // Pausing stops time
    fireEvent.click(button(container, "pause"));
    const pausedEnd = trajectories()[0].dataset.end;
    step(1000);
    expect(trajectories()[0].dataset.end).toBe(pausedEnd);
  });

  it("adjusts the playback speed within its limits", () => {
    const { container } = render(
      <TrajectoryVisualizer fieldImg="/f.png" data={data} />
    );
    fireEvent.click(button(container, "forward"));
    expect(screen.getByText("10x")).toBeTruthy();
    expect(button(container, "forward").disabled).toBe(true);
    fireEvent.click(button(container, "forward"));
    expect(screen.getByText("10x")).toBeTruthy();

    fireEvent.click(button(container, "play"));
    step(1000);
    expectNear(trajectories()[0].dataset.end, 100, 4);
    fireEvent.click(button(container, "pause"));

    fireEvent.click(button(container, "backward"));
    fireEvent.click(button(container, "backward"));
    expect(screen.getByText("1x")).toBeTruthy();
    expect(button(container, "backward").disabled).toBe(true);
    fireEvent.click(button(container, "backward"));
    expect(screen.getByText("1x")).toBeTruthy();

    fireEvent.click(button(container, "play"));
    const before = Number(trajectories()[0].dataset.end);
    step(1000);
    expectNear(Number(trajectories()[0].dataset.end) - before, 10, 1);
  });

  it("scrubs with the slider and returns to the full match", () => {
    const { container } = render(
      <TrajectoryVisualizer fieldImg="/f.png" data={data} />
    );
    fireEvent.click(button(container, "play"));
    fireEvent.change(container.querySelector('input[type="range"]'), {
      target: { value: "754" },
    });
    expect(button(container, "play")).toBeTruthy();
    expect(trajectories()[0].dataset.start).toBe("704");
    expect(trajectories()[0].dataset.end).toBe("754");
    expect(clock(container)).toBe("01:15");

    fireEvent.click(button(container, "eye-open"));
    expect(trajectories()[0].dataset.start).toBe("0");
    expect(trajectories()[0].dataset.end).toBe("1500");
    expect(clock(container)).toBe("00:00");
  });

  it("stops animating when unmounted", () => {
    const cancel = jest.spyOn(window, "cancelAnimationFrame");
    const { unmount } = render(
      <TrajectoryVisualizer fieldImg="/f.png" data={data} />
    );
    unmount();
    expect(cancel).toHaveBeenCalled();
    cancel.mockRestore();
  });

  it("does not cancel an animation frame that was never requested", () => {
    const cancel = jest.spyOn(window, "cancelAnimationFrame");
    const raf = jest
      .spyOn(window, "requestAnimationFrame")
      .mockImplementation(() => 0);
    const { unmount } = render(
      <TrajectoryVisualizer fieldImg="/f.png" data={data} />
    );
    unmount();
    expect(cancel).not.toHaveBeenCalled();
    raf.mockRestore();
    cancel.mockRestore();
  });
});
