/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";
import TwitchIcon from "../TwitchIcon";
import YouTubeIcon from "../YouTubeIcon";

describe("TwitchIcon", () => {
  it("renders the twitch glyph with the given style", () => {
    const { container } = render(<TwitchIcon style={{ color: "red" }} />);
    const svg = container.querySelector("svg");
    expect(svg.getAttribute("viewBox")).toBe("0 0 512 512");
    expect(svg.style.color).toBe("red");
    expect(svg.querySelector("path")).not.toBeNull();
  });
});

describe("YouTubeIcon", () => {
  it("renders the youtube glyph with the given style", () => {
    const { container } = render(<YouTubeIcon style={{ color: "blue" }} />);
    const svg = container.querySelector("svg");
    expect(svg.getAttribute("viewBox")).toBe("0 0 576 512");
    expect(svg.style.color).toBe("blue");
    expect(svg.querySelector("path")).not.toBeNull();
  });
});
