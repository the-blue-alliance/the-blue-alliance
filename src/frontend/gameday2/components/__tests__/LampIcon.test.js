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

  it("applies the default 48x48 size when none is given", () => {
    // React 19 ignores defaultProps on function components.
    const { container } = render(<LampIcon />);
    const svg = container.querySelector("svg");
    expect(svg.getAttribute("width")).toBe("48");
    expect(svg.getAttribute("height")).toBe("48");
  });
});
