/* @jest-environment jsdom */

import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import HeatmapVisualizer from "../HeatmapVisualizer";

const mockCreate = jest.fn();
jest.mock("heatmap.js", () => ({
  __esModule: true,
  default: { create: (cfg) => mockCreate(cfg) },
}));

const data = {
  times: [0, 1, 2],
  alliances: {
    red: [
      { team_key: "frc254", xs: [1, 1, null], ys: [2, 2, 2] },
      { team_key: "frc604", xs: [10, 54, 10], ys: [5, 5, 27] },
      { team_key: "frc1678", xs: [], ys: [] },
    ],
    blue: [
      { team_key: "frc971", xs: [53.9, null, null], ys: [26.9, null, null] },
      { team_key: "frc973", xs: [], ys: [] },
      { team_key: "frc1323", xs: [], ys: [] },
    ],
  },
};

describe("HeatmapVisualizer", () => {
  let setData;
  let widthSpy;
  let heightSpy;

  beforeEach(() => {
    setData = jest.fn();
    mockCreate.mockReset();
    mockCreate.mockReturnValue({ setData });
    widthSpy = jest
      .spyOn(HTMLElement.prototype, "offsetWidth", "get")
      .mockReturnValue(540);
    heightSpy = jest
      .spyOn(HTMLElement.prototype, "offsetHeight", "get")
      .mockReturnValue(270);
  });

  afterEach(() => {
    widthSpy.mockRestore();
    heightSpy.mockRestore();
  });

  const lastData = () => setData.mock.calls[setData.mock.calls.length - 1][0];

  it("plots every team's in-bounds positions until a team is selected", () => {
    const { container } = render(
      <HeatmapVisualizer fieldImg="/images/2019_field.png" data={data} />
    );
    const svg = container.querySelector("svg");
    expect(mockCreate).toHaveBeenCalledWith({ container: svg.parentElement });
    expect(lastData()).toEqual({
      min: 0,
      max: 2,
      data: [
        { x: 10, y: 250, value: 2 },
        { x: 100, y: 220, value: 1 },
        { x: 535, y: 5, value: 1 },
      ],
    });
  });

  it("toggles individual teams on and off", () => {
    render(<HeatmapVisualizer fieldImg="/f.png" data={data} />);
    const red = screen.getByText("254");
    const blue = screen.getByText("971");

    fireEvent.click(red);
    expect(red.className).toBe("btn btn-tiny active");
    expect(lastData().data).toEqual([{ x: 10, y: 250, value: 2 }]);

    fireEvent.click(blue);
    expect(blue.className).toBe("btn btn-tiny active");
    expect(lastData().data).toHaveLength(2);

    fireEvent.click(red);
    expect(red.className).toBe("btn btn-tiny");
    expect(lastData().data).toEqual([{ x: 535, y: 5, value: 1 }]);

    // Deselecting the last team goes back to showing everyone
    fireEvent.click(blue);
    expect(blue.className).toBe("btn btn-tiny");
    expect(lastData().data).toHaveLength(3);
  });
});
