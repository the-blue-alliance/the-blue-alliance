/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";
import LampIcon from "../LampIcon";

describe("LampIcon", () => {
  it("renders the TBA lamp at the requested size", () => {
    const { container } = render(<LampIcon width={36} height="2em" />);
    const svg = container.querySelector("svg");
    expect(svg.getAttribute("width")).toBe("36");
    expect(svg.getAttribute("height")).toBe("2em");
    expect(svg.getAttribute("viewBox")).toBe("0 0 240 240");
    expect(svg.querySelectorAll("path")).toHaveLength(8);
  });

  it("renders the lamp when no size is given", () => {
    const { container } = render(<LampIcon />);
    const svg = container.querySelector("svg");
    expect(svg.getAttribute("viewBox")).toBe("0 0 240 240");
  });

  it("Bug #68: applies the default 48x48 size when none is given", () => {
    // Wrong today: LampIcon declares defaultProps of 48x48, but React 19 no
    // longer applies defaultProps to function components, so the svg has no
    // width or height at all.
    // Correct: the default size is applied (e.g. via default parameters).
    const { container } = render(<LampIcon />);
    const svg = container.querySelector("svg");
    expect(svg.getAttribute("width")).toBe("48");
    expect(svg.getAttribute("height")).toBe("48");
  });
});
