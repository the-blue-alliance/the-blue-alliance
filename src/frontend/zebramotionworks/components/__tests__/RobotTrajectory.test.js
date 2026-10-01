/* @jest-environment jsdom */

import React from "react";
import { render } from "@testing-library/react";
import RobotTrajectory from "../RobotTrajectory";

const renderTrajectory = (props) =>
  render(
    <svg>
      <RobotTrajectory color="#FF0000" {...props} />
    </svg>
  ).container;

const teamData = {
  team_key: "frc254",
  xs: [null, 1, 2, 3, null],
  ys: [null, 10, 12, 14, null],
};

const indicator = (container) => {
  const circle = container.querySelector("circle");
  return circle && [circle.getAttribute("cx"), circle.getAttribute("cy")];
};

describe("RobotTrajectory", () => {
  it("draws the path between the start and end times, skipping gaps", () => {
    const container = renderTrajectory({
      teamData,
      startTime: 0,
      endTime: 5,
      indicatorAtStart: true,
    });
    const path = container.querySelector("path");
    expect(path.getAttribute("d")).toBe("M 1 17 L 1 17 L 2 15 L 3 13");
    expect(path.getAttribute("stroke")).toBe("#FF0000");
    expect(container.querySelector("text").textContent).toBe("254");
  });

  it("interpolates the indicator position at the start time", () => {
    const container = renderTrajectory({
      teamData,
      startTime: 1.5,
      endTime: 3,
      indicatorAtStart: true,
    });
    expect(indicator(container)).toEqual(["1.5", "16"]);
  });

  it("includes the sample at the (floored) end time in the path", () => {
    // Every sample from ceil(start) through floor(end) is drawn.
    const container = renderTrajectory({
      teamData,
      startTime: 1.5,
      endTime: 3,
      indicatorAtStart: true,
    });
    expect(container.querySelector("path").getAttribute("d")).toBe(
      "M 2 15 L 2 15 L 3 13"
    );
  });

  it("falls back to the first known position after the start time", () => {
    const container = renderTrajectory({
      teamData,
      startTime: 0,
      endTime: 4,
      indicatorAtStart: true,
    });
    expect(indicator(container)).toEqual(["1", "17"]);
  });

  it("interpolates the indicator position at the end time", () => {
    const container = renderTrajectory({
      teamData,
      startTime: 0,
      endTime: 2.5,
    });
    expect(indicator(container)).toEqual(["2.5", "14"]);
  });

  it("falls back to the last known position before the end time", () => {
    const container = renderTrajectory({
      teamData,
      startTime: 0,
      endTime: 4,
    });
    expect(indicator(container)).toEqual(["3", "13"]);
  });

  it("omits the indicator when there is no known position", () => {
    const container = renderTrajectory({
      teamData: { team_key: "frc1", xs: [null, null], ys: [null, null] },
      startTime: 0,
      endTime: 1,
      indicatorAtStart: true,
    });
    expect(container.querySelector("circle")).toBeNull();
    expect(container.querySelector("text")).toBeNull();
    expect(container.querySelector("path").getAttribute("d")).toBe("");
  });
});
