/* @jest-environment jsdom */
import React from "react";
import { format } from "util";
import { render, fireEvent, act } from "@testing-library/react";
import LayoutSelectionPanel from "../LayoutSelectionPanel";
import {
  NUM_LAYOUTS,
  LAYOUT_DISPLAY_ORDER,
  NAME_FOR_LAYOUT,
} from "../../constants/LayoutConstants";

// jsdom does no layout, so offsetHeight is derived from the element's role in
// the panel: the full-size outer component, the title, or the list wrapper.
// Tests set `heights` before rendering so componentDidMount measures them too.
let heights = { component: 0, title: 0, list: 0 };
const originalOffsetHeight = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  "offsetHeight"
);

beforeAll(() => {
  Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
    configurable: true,
    get() {
      if (this.tagName === "H3") {
        return heights.title;
      }
      if (this.style.height === "100%" && this.style.width === "100%") {
        return heights.component;
      }
      if (this.firstChild && this.firstChild.tagName === "UL") {
        return heights.list;
      }
      return 0;
    },
  });
});

afterAll(() => {
  Object.defineProperty(
    HTMLElement.prototype,
    "offsetHeight",
    originalOffsetHeight
  );
});

beforeEach(() => {
  heights = { component: 1000, title: 60, list: 500 };
});

const getListContainer = (container) =>
  container.querySelector("h3").nextSibling;

describe("Bug #35: LayoutSelectionPanel ListItem button prop", () => {
  // Must run before any other test in this file: React only warns about a
  // given unknown DOM attribute once per module registry.
  it("Bug #35: does not pass MUI's removed `button` prop through to the DOM", () => {
    // Wrong today: ListItem lost its `button` prop in MUI v7, so `button` is
    // forwarded to the <li> and React warns about an unknown attribute.
    // Correct: use ListItemButton (or drop the prop); no warning, no attribute.
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    try {
      render(<LayoutSelectionPanel setLayout={() => {}} />);
      expect(document.querySelector("[button]")).toBeNull();
      const buttonWarnings = spy.mock.calls
        .map((args) => format(...args))
        .filter((msg) => msg.includes("`button`"));
      expect(buttonWarnings).toEqual([]);
    } finally {
      spy.mockRestore();
    }
  });
});

describe("LayoutSelectionPanel", () => {
  it("lists every layout in display order with its icon", () => {
    const { container, getByText } = render(
      <LayoutSelectionPanel setLayout={() => {}} />
    );
    expect(getByText("Select a layout")).toBeTruthy();
    const items = container.querySelectorAll("ul > li");
    expect(items).toHaveLength(NUM_LAYOUTS);
    items.forEach((item, i) => {
      expect(item.textContent).toBe(NAME_FOR_LAYOUT[LAYOUT_DISPLAY_ORDER[i]]);
      expect(item.querySelector("svg path")).not.toBeNull();
    });
  });

  it("selects a layout when its item is clicked", () => {
    const setLayout = jest.fn();
    const { getByText } = render(
      <LayoutSelectionPanel setLayout={setLayout} />
    );
    fireEvent.click(getByText("Horizontal Split View"));
    expect(setLayout).toHaveBeenCalledWith(9);
  });

  it("leaves the list unconstrained when it fits within the panel", () => {
    const { container } = render(<LayoutSelectionPanel setLayout={() => {}} />);
    const listContainer = getListContainer(container);
    expect(listContainer.style.height).toBe("");
    expect(listContainer.style.overflowY).toBe("");
  });

  it("constrains and scrolls the list when it overflows the panel", () => {
    heights = { component: 400, title: 60, list: 500 };
    const { container } = render(<LayoutSelectionPanel setLayout={() => {}} />);
    const listContainer = getListContainer(container);
    // 400 - 2 * 20 margin - 60 title = 300
    expect(listContainer.style.height).toBe("300px");
    expect(listContainer.style.overflowY).toBe("auto");
  });

  it("re-measures on window resize", () => {
    const { container } = render(<LayoutSelectionPanel setLayout={() => {}} />);
    const listContainer = getListContainer(container);
    expect(listContainer.style.height).toBe("");

    heights = { component: 400, title: 60, list: 500 };
    act(() => {
      window.dispatchEvent(new Event("resize"));
    });
    expect(listContainer.style.height).toBe("300px");

    // Growing the panel releases the height constraint again
    heights = { component: 1000, title: 60, list: 500 };
    act(() => {
      window.dispatchEvent(new Event("resize"));
    });
    expect(listContainer.style.height).toBe("");
  });

  it("re-measures after re-rendering", () => {
    const { container, rerender } = render(
      <LayoutSelectionPanel setLayout={() => {}} />
    );
    const listContainer = getListContainer(container);
    heights = { component: 400, title: 60, list: 500 };
    rerender(<LayoutSelectionPanel setLayout={() => {}} />);
    expect(listContainer.style.height).toBe("300px");
  });

  it("stops listening for resizes after unmount", () => {
    const { container, unmount } = render(
      <LayoutSelectionPanel setLayout={() => {}} />
    );
    const listContainer = getListContainer(container);
    unmount();
    heights = { component: 400, title: 60, list: 500 };
    act(() => {
      window.dispatchEvent(new Event("resize"));
    });
    expect(listContainer.style.height).toBe("");
  });
});
