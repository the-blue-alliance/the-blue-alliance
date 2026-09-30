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

  it("renders without a size when none is given", () => {
    // LampIcon declares defaultProps of 48x48, but React 19 no longer applies
    // defaultProps to function components, so the attributes are simply
    // absent. AppBar always passes explicit sizes, so nothing user-visible
    // depends on the default.
    const { container } = render(<LampIcon />);
    const svg = container.querySelector("svg");
    expect(svg.getAttribute("width")).toBeNull();
    expect(svg.getAttribute("height")).toBeNull();
    expect(LampIcon.defaultProps).toEqual({ width: 48, height: 48 });
  });
});
