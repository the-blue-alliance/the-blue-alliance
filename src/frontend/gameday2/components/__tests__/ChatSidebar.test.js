/* @jest-environment jsdom */
import React from "react";
import { render, fireEvent, act } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";

jest.mock("react-ga4", () => ({
  __esModule: true,
  default: { event: jest.fn() },
}));

import ReactGA from "react-ga4";
import ChatSidebar from "../ChatSidebar";

const theme = createTheme({
  layout: { appBarHeight: 36, socialPanelWidth: 300, chatPanelWidth: 320 },
});

const chats = {
  firstupdatesnow: { name: "FIRST Updates Now", channel: "firstupdatesnow" },
  firstinspires: { name: "FIRST", channel: "firstinspires" },
  svr: { name: "Silicon Valley Regional", channel: "svr" },
};

const renderSidebar = (props = {}) => {
  const allProps = {
    enabled: true,
    hasBeenVisible: true,
    chats,
    displayOrderChats: Object.values(chats),
    renderedChats: ["firstupdatesnow", "svr"],
    currentChat: "svr",
    defaultChat: "firstupdatesnow",
    setTwitchChat: jest.fn(),
    setChatSidebarVisibility: jest.fn(),
    setHashtagSidebarVisibility: jest.fn(),
    ...props,
  };
  const utils = render(
    <ThemeProvider theme={theme}>
      <ChatSidebar {...allProps} />
    </ThemeProvider>
  );
  return { ...utils, props: allProps };
};

const setWindowWidth = (width) => {
  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    writable: true,
    value: width,
  });
};

describe("ChatSidebar", () => {
  beforeEach(() => {
    setWindowWidth(1280);
    ReactGA.event.mockClear();
  });

  it("renders an empty placeholder until it has been visible once", () => {
    const { container } = renderSidebar({ hasBeenVisible: false });
    expect(container.innerHTML).toBe("<div></div>");
  });

  it("renders each rendered chat, showing only the current one", () => {
    const { container } = renderSidebar();
    const iframes = container.querySelectorAll("iframe");
    expect(iframes).toHaveLength(2);
    expect(iframes[0].id).toBe("twich-chat-firstupdatesnow");
    expect(iframes[0].parentNode.style.display).toBe("none");
    expect(iframes[1].id).toBe("twich-chat-svr");
    expect(iframes[1].parentNode.style.display).toBe("");
  });

  it("positions the panel from the theme and hides it when disabled", () => {
    const { container } = renderSidebar();
    const panel = container.firstChild;
    expect(panel.style.top).toBe("36px");
    expect(panel.style.width).toBe("320px");
    expect(panel.style.display).toBe("");

    const disabled = renderSidebar({ enabled: false });
    expect(disabled.container.firstChild.style.display).toBe("none");
  });

  it("titles the switcher after the current chat", () => {
    expect(
      renderSidebar().getByText("Silicon Valley Regional Chat")
    ).toBeTruthy();
    expect(
      renderSidebar({ currentChat: "firstupdatesnow" }).getByText(
        "TBA GameDay / FUN"
      )
    ).toBeTruthy();
    expect(
      renderSidebar({
        currentChat: "firstinspires",
        defaultChat: "firstinspires",
      }).getByText("TBA GameDay / FIRST")
    ).toBeTruthy();
    // A non-default FIRST chat keeps its own name
    expect(
      renderSidebar({ currentChat: "firstinspires" }).getByText("FIRST Chat")
    ).toBeTruthy();
    expect(
      renderSidebar({ currentChat: "missing" }).getByText("UNKNOWN")
    ).toBeTruthy();
  });

  it("opens the chat selector from the switcher and closes it on selection", () => {
    const { container, getByText, queryByText, props } = renderSidebar();
    expect(queryByText("FIRST")).toBeNull();

    fireEvent.click(container.querySelector(".MuiToolbar-root"));
    expect(getByText("FIRST")).toBeTruthy();

    fireEvent.click(getByText("FIRST"));
    expect(props.setTwitchChat).toHaveBeenCalledWith("firstinspires");
  });

  it("tracks the current chat only while enabled", () => {
    renderSidebar();
    expect(ReactGA.event).toHaveBeenCalledWith(
      expect.objectContaining({ category: "Selected Chat Time", action: "svr" })
    );

    ReactGA.event.mockClear();
    renderSidebar({ enabled: false });
    expect(ReactGA.event).not.toHaveBeenCalled();
  });

  it("collapses both sidebars on narrow windows, on mount and on resize", () => {
    const { props } = renderSidebar();
    expect(props.setChatSidebarVisibility).not.toHaveBeenCalled();

    act(() => {
      setWindowWidth(600);
      window.dispatchEvent(new Event("resize"));
    });
    expect(props.setChatSidebarVisibility).toHaveBeenCalledWith(false);
    expect(props.setHashtagSidebarVisibility).toHaveBeenCalledWith(false);

    setWindowWidth(500);
    const narrow = renderSidebar();
    expect(narrow.props.setChatSidebarVisibility).toHaveBeenCalledWith(false);
    expect(narrow.props.setHashtagSidebarVisibility).toHaveBeenCalledWith(
      false
    );
  });

  it("stops listening for resizes after unmount", () => {
    const { props, unmount } = renderSidebar();
    unmount();
    act(() => {
      setWindowWidth(600);
      window.dispatchEvent(new Event("resize"));
    });
    expect(props.setChatSidebarVisibility).not.toHaveBeenCalled();
  });
});
