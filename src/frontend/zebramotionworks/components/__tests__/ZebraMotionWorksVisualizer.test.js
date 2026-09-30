/* @jest-environment jsdom */

import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import ZebraMotionWorksVisualizer from "../ZebraMotionWorksVisualizer";

jest.mock("../TrajectoryVisualizer", () => (props) => (
  <div data-testid="trajectory" data-field={props.fieldImg} />
));
jest.mock("../HeatmapVisualizer", () => (props) => (
  <div data-testid="heatmap" data-field={props.fieldImg} />
));

describe("ZebraMotionWorksVisualizer", () => {
  it("switches between the trajectory and heatmap views", () => {
    render(<ZebraMotionWorksVisualizer data={{}} year={2019} />);
    const trajButton = screen.getByText("Trajectory");
    const heatButton = screen.getByText("Heatmap");

    expect(trajButton.className).toBe("btn btn-secondary active");
    expect(heatButton.className).toBe("btn btn-secondary");
    expect(screen.getByTestId("trajectory").dataset.field).toBe(
      "/images/2019_field.png"
    );
    expect(screen.queryByTestId("heatmap")).toBeNull();
    fireEvent.click(heatButton);
    expect(heatButton.className).toBe("btn btn-secondary active");
    expect(trajButton.className).toBe("btn btn-secondary");
    expect(screen.getByTestId("heatmap").dataset.field).toBe(
      "/images/2019_field.png"
    );
    expect(screen.queryByTestId("trajectory")).toBeNull();

    fireEvent.click(trajButton);
    expect(screen.getByTestId("trajectory")).toBeTruthy();
    expect(screen.queryByTestId("heatmap")).toBeNull();
  });
});
