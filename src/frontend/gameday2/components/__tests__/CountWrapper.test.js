/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";

jest.mock("react-countup", () => (props) => (
  <span data-testid="countup" data-start={props.start} data-end={props.end} />
));

import CountWrapper from "../CountWrapper";

describe("CountWrapper", () => {
  it("starts and ends at the initial number", () => {
    const { getByTestId } = render(<CountWrapper number={42} />);
    const countup = getByTestId("countup");
    expect(countup.getAttribute("data-start")).toBe("42");
    expect(countup.getAttribute("data-end")).toBe("42");
  });

  it("animates from the previous number to the new one", () => {
    const { getByTestId, rerender } = render(<CountWrapper number={10} />);
    rerender(<CountWrapper number={25} />);
    const countup = getByTestId("countup");
    expect(countup.getAttribute("data-start")).toBe("10");
    expect(countup.getAttribute("data-end")).toBe("25");

    rerender(<CountWrapper number={40} />);
    expect(countup.getAttribute("data-start")).toBe("25");
    expect(countup.getAttribute("data-end")).toBe("40");
  });
});
