/* @jest-environment jsdom */
import React from "react";
import { render, act } from "@testing-library/react";

// element-resize-event injects a resize sensor into the page; capture the
// callbacks instead so tests can fire them on demand.
const mockResizeCallbacks = new Map();
jest.mock("element-resize-event", () => (element, callback) => {
  mockResizeCallbacks.set(element, callback);
});

import AutoScale from "../AutoScale";

// jsdom does no layout, so drive offsetWidth/offsetHeight from a lookup.
const sizes = new Map();
const originalWidth = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  "offsetWidth"
);
const originalHeight = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  "offsetHeight"
);

beforeAll(() => {
  Object.defineProperty(HTMLElement.prototype, "offsetWidth", {
    configurable: true,
    get() {
      return (sizes.get(this) || { width: 0 }).width;
    },
  });
  Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
    configurable: true,
    get() {
      return (sizes.get(this) || { height: 0 }).height;
    },
  });
});

afterAll(() => {
  Object.defineProperty(HTMLElement.prototype, "offsetWidth", originalWidth);
  Object.defineProperty(HTMLElement.prototype, "offsetHeight", originalHeight);
});

beforeEach(() => {
  sizes.clear();
  mockResizeCallbacks.clear();
});

// Sizes are read in componentDidMount, so they must be known before the
// component mounts. The wrapper and content are located by class name in a
// ref callback that runs before componentDidMount.
const renderScaled = (props, wrapperSize, contentSize) => {
  const Sized = () => (
    <AutoScale
      wrapperClass="wrapper"
      containerClass="container"
      contentClass="content"
      {...props}
    >
      <div
        className="inner"
        ref={(el) => {
          if (el) {
            sizes.set(el, contentSize);
            sizes.set(el.parentNode.parentNode.parentNode, wrapperSize);
          }
        }}
      />
    </AutoScale>
  );
  const utils = render(<Sized />);
  const wrapper = utils.container.querySelector(".wrapper");
  const container = utils.container.querySelector(".container");
  const content = utils.container.querySelector(".content");
  const inner = utils.container.querySelector(".inner");
  return { ...utils, wrapper, container, content, inner };
};

describe("AutoScale", () => {
  it("scales the content to fit the wrapper", () => {
    const { wrapper, container, content } = renderScaled(
      {},
      { width: 400, height: 400 },
      { width: 800, height: 200 }
    );
    expect(wrapper.className).toBe("wrapper");
    // min(400/800, 400/200) = 0.5
    expect(content.style.transform).toBe("scale(0.5)");
    expect(content.style.transformOrigin).toBe("0 0 0");
    expect(container.style.width).toBe("400px");
    expect(container.style.height).toBe("100px");
  });

  it("applies the default empty class names", () => {
    const { container } = render(
      <AutoScale>
        <div />
      </AutoScale>
    );
    expect(container.firstChild.className).toBe("");
    expect(container.firstChild.firstChild.className).toBe("");
  });

  it("caps the scale by maxHeight, maxWidth and maxScale", () => {
    // Unconstrained scale would be min(1600/800, 800/200) = 2
    const large = { width: 1600, height: 800 };
    const content = { width: 800, height: 200 };

    expect(
      renderScaled({ maxHeight: 100 }, large, content).content.style.transform
    ).toBe("scale(0.5)");
    expect(
      renderScaled({ maxWidth: 400 }, large, content).content.style.transform
    ).toBe("scale(0.5)");
    expect(
      renderScaled({ maxScale: 1.5 }, large, content).content.style.transform
    ).toBe("scale(1.5)");
    expect(renderScaled({}, large, content).content.style.transform).toBe(
      "scale(2)"
    );
  });

  it("rescales when the content or wrapper is resized", () => {
    const { wrapper, content, inner } = renderScaled(
      {},
      { width: 400, height: 400 },
      { width: 800, height: 200 }
    );
    expect(content.style.transform).toBe("scale(0.5)");

    act(() => {
      sizes.set(inner, { width: 400, height: 200 });
      mockResizeCallbacks.get(inner)();
    });
    expect(content.style.transform).toBe("scale(1)");

    act(() => {
      sizes.set(wrapper, { width: 200, height: 400 });
      mockResizeCallbacks.get(wrapper)();
    });
    expect(content.style.transform).toBe("scale(0.5)");
  });

  it("requires exactly one child", () => {
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    expect(() =>
      render(
        <AutoScale>
          <div />
          <div />
        </AutoScale>
      )
    ).toThrow();
    spy.mockRestore();
  });
});
