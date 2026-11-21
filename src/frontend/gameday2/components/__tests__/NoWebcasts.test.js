/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";
import NoWebcasts from "../NoWebcasts";

describe("NoWebcasts", () => {
  it("explains there are no webcasts and links back to TBA", () => {
    const { getByText, getByRole } = render(<NoWebcasts />);
    expect(getByText("No webcasts found")).toBeTruthy();
    expect(
      getByRole("link", { name: "Go to The Blue Alliance" }).getAttribute(
        "href"
      )
    ).toBe("https://www.thebluealliance.com");
  });
});
