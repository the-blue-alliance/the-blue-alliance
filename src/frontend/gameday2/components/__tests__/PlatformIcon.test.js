/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";
import PlatformIcon from "../PlatformIcon";

describe("PlatformIcon", () => {
  it("renders the YouTube icon for youtube webcasts", () => {
    const { container } = render(<PlatformIcon platform="youtube" />);
    expect(container.querySelector("svg").getAttribute("viewBox")).toBe(
      "0 0 576 512"
    );
  });

  it("renders the Twitch icon for twitch webcasts", () => {
    const { container } = render(<PlatformIcon platform="twitch" />);
    expect(container.querySelector("svg").getAttribute("viewBox")).toBe(
      "0 0 512 512"
    );
  });

  it("renders nothing for platforms without a logo", () => {
    const { container } = render(<PlatformIcon platform="ustream" />);
    expect(container.innerHTML).toBe("");
  });
});
