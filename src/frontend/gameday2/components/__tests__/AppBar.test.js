/* @jest-environment jsdom */
import React from "react";
import { render, fireEvent } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import AppBar from "../AppBar";

const theme = createTheme({
  layout: { appBarHeight: 36, socialPanelWidth: 300, chatPanelWidth: 300 },
  appBar: { textColor: "#ffffff" },
});

const renderAppBar = (props = {}) => {
  const allProps = {
    webcasts: ["2026casj-0"],
    hashtagSidebarVisible: false,
    chatSidebarVisible: false,
    resetWebcasts: jest.fn(),
    toggleHashtagSidebarVisibility: jest.fn(),
    toggleChatSidebarVisibility: jest.fn(),
    setLayout: jest.fn(),
    layoutId: 0,
    layoutSet: true,
    layoutDrawerVisible: false,
    setLayoutDrawerVisibility: jest.fn(),
    ...props,
  };
  const utils = render(
    <ThemeProvider theme={theme}>
      <AppBar {...allProps} />
    </ThemeProvider>
  );
  return { ...utils, props: allProps };
};

describe("AppBar", () => {
  it("renders the TBA branding, title and facebook like button", () => {
    const { getByText, container, getAllByRole } = renderAppBar();
    expect(getByText("GameDay")).toBeTruthy();
    expect(getByText("by The Blue Alliance").getAttribute("href")).toBe("/");
    expect(container.querySelector(".fb-like")).not.toBeNull();

    const brandingLink = getAllByRole("link").find(
      (link) => link.getAttribute("href") === "https://www.thebluealliance.com"
    );
    expect(brandingLink).toBeTruthy();
    const lamp = brandingLink.querySelector("svg");
    expect(lamp.getAttribute("width")).toBe("36");
    expect(lamp.getAttribute("height")).toBe("36");

    const toolbar = container.querySelector(".MuiToolbar-root");
    expect(toolbar.style.height).toBe("36px");
    expect(toolbar.style.minHeight).toBe("36px");
  });

  it("opens the layout drawer from the configure button", () => {
    const { getByText, props } = renderAppBar();
    fireEvent.click(getByText("Configure Layout"));
    expect(props.setLayoutDrawerVisibility).toHaveBeenCalledWith(true);
  });

  it("renders the layout drawer closed by default and open when requested", () => {
    const { queryByText } = renderAppBar();
    expect(queryByText("Select video grid layout")).toBeNull();

    const { getByText, props } = renderAppBar({ layoutDrawerVisible: true });
    expect(getByText("Select video grid layout")).toBeTruthy();
    fireEvent.click(getByText("Reset Webcasts"));
    expect(props.resetWebcasts).toHaveBeenCalledTimes(1);
  });

  it("tells the drawer there are no webcasts when the list is empty", () => {
    const { getByText } = renderAppBar({
      webcasts: [],
      layoutDrawerVisible: true,
    });
    expect(
      getByText(
        "There aren't any webcasts available right now. Check back later!"
      )
    ).toBeTruthy();
  });
});
