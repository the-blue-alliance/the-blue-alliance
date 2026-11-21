/* @jest-environment jsdom */

import React from "react";
import { render } from "@testing-library/react";
import PowerupCount from "../PowerupCount";

describe("PowerupCount", () => {
  it("renders an empty, unplayed powerup", () => {
    const { container } = render(
      <PowerupCount color="red" type="force" count={0} played={false} />
    );
    const root = container.firstChild;
    expect(root.className.split(/\s+/).filter(Boolean)).toEqual([
      "powerupCountContainer",
    ]);
    const icon = root.querySelector("img");
    expect(icon.getAttribute("src")).toBe("/images/2018_force.png");
    expect(icon.getAttribute("title")).toBe("Force");
    expect(root.querySelectorAll(".powerCubeActive")).toHaveLength(0);
  });

  it.each([1, 2, 3])("shows %i active cubes", (count) => {
    const { container } = render(
      <PowerupCount color="blue" type="boost" count={count} played isCenter />
    );
    const root = container.firstChild;
    expect(root.classList).toContain("powerupCountContainerCenter");
    expect(root.classList).toContain(`blueCount${count}`);
    expect(root.classList).toContain("blue");
    expect(root.querySelectorAll(".powerCubeActive")).toHaveLength(count);
  });
});
