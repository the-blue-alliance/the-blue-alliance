/* @jest-environment jsdom */
import React from "react";
import { format } from "util";
import { render, fireEvent } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import LayoutDrawer from "../LayoutDrawer";
import {
  NUM_LAYOUTS,
  LAYOUT_DISPLAY_ORDER,
  NAME_FOR_LAYOUT,
} from "../../constants/LayoutConstants";

const theme = createTheme({
  layout: { appBarHeight: 36, socialPanelWidth: 300, chatPanelWidth: 300 },
});

const renderDrawer = (props = {}) => {
  const allProps = {
    setLayout: jest.fn(),
    selectedLayout: 3,
    layoutSet: true,
    hashtagSidebarVisible: false,
    chatSidebarVisible: true,
    layoutDrawerVisible: true,
    setLayoutDrawerVisibility: jest.fn(),
    hasWebcasts: true,
    toggleChatSidebarVisibility: jest.fn(),
    toggleHashtagSidebarVisibility: jest.fn(),
    resetWebcasts: jest.fn(),
    ...props,
  };
  const utils = render(
    <ThemeProvider theme={theme}>
      <LayoutDrawer {...allProps} />
    </ThemeProvider>
  );
  return { ...utils, props: allProps };
};

describe("LayoutDrawer ListItem button prop", () => {
  // Runs first: React warns about a given unknown DOM attribute only once per module registry.
  it("does not pass MUI's removed `button` prop through to the DOM", () => {
    // MUI v7 ListItem has no `button` prop; React warns if it reaches the DOM.
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    try {
      renderDrawer();
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

describe("LayoutDrawer", () => {
  it("lists the layouts in display order and checks the selected one", () => {
    const { getByText, container } = renderDrawer();
    const layoutList =
      container.ownerDocument.querySelectorAll(".MuiList-root")[0];
    const items = layoutList.querySelectorAll(
      ":scope > li.MuiListItem-container"
    );
    expect(items).toHaveLength(NUM_LAYOUTS);
    items.forEach((item, i) => {
      expect(item.textContent).toBe(NAME_FOR_LAYOUT[LAYOUT_DISPLAY_ORDER[i]]);
      expect(item.querySelector("svg")).not.toBeNull();
    });
    const quad = getByText("Quad View").closest("li");
    expect(quad.querySelector('[data-testid="CheckIcon"]')).not.toBeNull();
    const single = getByText("Single View").closest("li");
    expect(single.querySelector('[data-testid="CheckIcon"]')).toBeNull();
  });

  it("does not check the selected layout until a layout has been set", () => {
    const { container } = renderDrawer({ layoutSet: false });
    expect(
      container.ownerDocument.querySelector('[data-testid="CheckIcon"]')
    ).toBeNull();
  });

  it("selects a layout when its item is clicked", () => {
    const { getByText, props } = renderDrawer();
    fireEvent.click(getByText("Hex View"));
    expect(props.setLayout).toHaveBeenCalledWith(6);
  });

  it("shows a message instead of layouts when there are no webcasts", () => {
    const { getByText, queryByText } = renderDrawer({ hasWebcasts: false });
    expect(
      getByText(
        "There aren't any webcasts available right now. Check back later!"
      )
    ).toBeTruthy();
    expect(queryByText("Single View")).toBeNull();
  });

  it("reflects and toggles the sidebar switches", () => {
    const { getAllByRole, props } = renderDrawer();
    const [hashtagSwitch, chatSwitch] = getAllByRole("switch");
    expect(hashtagSwitch.checked).toBe(false);
    expect(chatSwitch.checked).toBe(true);

    fireEvent.click(hashtagSwitch);
    expect(props.toggleHashtagSidebarVisibility).toHaveBeenCalledTimes(1);
    fireEvent.click(chatSwitch);
    expect(props.toggleChatSidebarVisibility).toHaveBeenCalledTimes(1);
  });

  it("resets the webcasts from the red button", () => {
    const { getByText, props } = renderDrawer();
    const button = getByText("Reset Webcasts").closest("button");
    expect(button.style.backgroundColor).toBe("rgb(244, 67, 54)");
    fireEvent.click(button);
    expect(props.resetWebcasts).toHaveBeenCalledTimes(1);
  });

  it("asks to be hidden when the drawer is dismissed", () => {
    const { container, props } = renderDrawer();
    fireEvent.click(container.ownerDocument.querySelector(".MuiBackdrop-root"));
    expect(props.setLayoutDrawerVisibility).toHaveBeenCalledWith(false);
  });

  it("positions the paper below the app bar", () => {
    const { container } = renderDrawer();
    const paper = container.ownerDocument.querySelector(".MuiDrawer-paper");
    expect(paper.style.width).toBe("300px");
    expect(paper.style.marginTop).toBe("36px");
  });

  it("renders nothing visible while closed", () => {
    const { queryByText } = renderDrawer({ layoutDrawerVisible: false });
    expect(queryByText("Select video grid layout")).toBeNull();
  });
});
