/* @jest-environment jsdom */
import React from "react";
import { render, act } from "@testing-library/react";
import AnimatableContainer from "../AnimatableContainer";

const beginStyle = { opacity: 0 };
const endStyle = { opacity: 1 };

describe("AnimatableContainer", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders children with the begin style merged over the base style", () => {
    const { container, getByText } = render(
      <AnimatableContainer
        beginStyle={beginStyle}
        endStyle={endStyle}
        style={{ position: "absolute", opacity: 0.5 }}
        className="overlay"
      >
        <span>child</span>
      </AnimatableContainer>
    );
    const div = container.firstChild;
    expect(getByText("child")).toBeTruthy();
    expect(div.className).toBe("overlay");
    expect(div.style.position).toBe("absolute");
    expect(div.style.opacity).toBe("0");
    // beginStyle/endStyle are not forwarded to the DOM element
    expect(div.hasAttribute("beginstyle")).toBe(false);
    expect(div.hasAttribute("endstyle")).toBe(false);
  });

  it("transitions to the end style on appear and calls back after 300ms", () => {
    const ref = React.createRef();
    const callback = jest.fn();
    const { container } = render(
      <AnimatableContainer
        ref={ref}
        beginStyle={beginStyle}
        endStyle={endStyle}
      />
    );

    act(() => {
      ref.current.componentWillAppear(callback);
    });
    expect(container.firstChild.style.opacity).toBe("0");

    act(() => {
      jest.advanceTimersByTime(0);
    });
    expect(container.firstChild.style.opacity).toBe("1");
    expect(callback).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(300);
    });
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it("treats enter the same as appear", () => {
    const ref = React.createRef();
    const callback = jest.fn();
    const { container } = render(
      <AnimatableContainer
        ref={ref}
        beginStyle={beginStyle}
        endStyle={endStyle}
      />
    );
    act(() => {
      ref.current.componentWillEnter(callback);
      jest.advanceTimersByTime(300);
    });
    expect(container.firstChild.style.opacity).toBe("1");
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it("returns to the begin style on leave and calls back after 300ms", () => {
    const ref = React.createRef();
    const callback = jest.fn();
    const { container } = render(
      <AnimatableContainer
        ref={ref}
        beginStyle={beginStyle}
        endStyle={endStyle}
      />
    );
    act(() => {
      ref.current.componentWillAppear(() => {});
      jest.advanceTimersByTime(300);
    });
    expect(container.firstChild.style.opacity).toBe("1");

    act(() => {
      ref.current.componentWillLeave(callback);
    });
    expect(container.firstChild.style.opacity).toBe("0");
    act(() => {
      jest.advanceTimersByTime(300);
    });
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it("cancels pending callbacks on unmount", () => {
    const ref = React.createRef();
    const enterCallback = jest.fn();
    const leaveCallback = jest.fn();
    const { unmount } = render(
      <AnimatableContainer
        ref={ref}
        beginStyle={beginStyle}
        endStyle={endStyle}
      />
    );
    act(() => {
      ref.current.componentWillAppear(enterCallback);
      ref.current.componentWillLeave(leaveCallback);
    });
    unmount();
    jest.advanceTimersByTime(1000);
    expect(enterCallback).not.toHaveBeenCalled();
    expect(leaveCallback).not.toHaveBeenCalled();
  });
});
