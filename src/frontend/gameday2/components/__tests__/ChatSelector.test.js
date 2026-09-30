/* @jest-environment jsdom */
import React from "react";
import { render, fireEvent } from "@testing-library/react";
import ChatSelector from "../ChatSelector";

const chats = [
  { name: "FIRST Updates Now", channel: "firstupdatesnow" },
  { name: "FIRST", channel: "firstinspires" },
  { name: "Silicon Valley Regional", channel: "svr" },
];

const renderSelector = (props = {}) =>
  render(
    <ChatSelector
      chats={chats}
      currentChat="svr"
      defaultChat="firstupdatesnow"
      setTwitchChat={() => {}}
      onRequestClose={() => {}}
      open
      {...props}
    />
  );

describe("ChatSelector", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders nothing while closed", () => {
    const { container } = renderSelector({ open: false });
    expect(container.firstChild.children).toHaveLength(0);
  });

  it("lists the chats, naming the default FUN chat after GameDay and checking the current one", () => {
    const { getByText, queryByText, getAllByRole } = renderSelector();
    expect(getByText("TBA GameDay / FUN")).toBeTruthy();
    expect(queryByText("FIRST Updates Now")).toBeNull();
    expect(getByText("FIRST")).toBeTruthy();
    expect(getByText("Silicon Valley Regional")).toBeTruthy();

    const items = getAllByRole("listitem");
    expect(items).toHaveLength(3);
    // Only the default chat gets the home icon
    expect(items[0].querySelector('[data-testid="HomeIcon"]')).not.toBeNull();
    expect(items[1].querySelector('[data-testid="HomeIcon"]')).toBeNull();
    // Only the current chat gets the check
    expect(items[2].querySelector('[data-testid="CheckIcon"]')).not.toBeNull();
    expect(items[0].querySelector('[data-testid="CheckIcon"]')).toBeNull();
  });

  it("names the default FIRST chat after GameDay too", () => {
    const { getByText, queryByText } = renderSelector({
      defaultChat: "firstinspires",
    });
    expect(getByText("TBA GameDay / FIRST")).toBeTruthy();
    expect(getByText("FIRST Updates Now")).toBeTruthy();
    expect(queryByText("FIRST")).toBeNull();
  });

  it("selects a chat and closes when an item is clicked", () => {
    const setTwitchChat = jest.fn();
    const onRequestClose = jest.fn();
    const { getByText } = renderSelector({ setTwitchChat, onRequestClose });
    fireEvent.click(getByText("FIRST"));
    expect(setTwitchChat).toHaveBeenCalledWith("firstinspires");
    // Closed once by the item, not a second time by the overlay (propagation
    // is stopped at the list)
    expect(onRequestClose).toHaveBeenCalledTimes(1);
  });

  it("closes without selecting when the overlay is clicked", () => {
    const setTwitchChat = jest.fn();
    const onRequestClose = jest.fn();
    const { container } = renderSelector({ setTwitchChat, onRequestClose });
    const overlay = container.firstChild.children[0];
    fireEvent.click(overlay);
    expect(onRequestClose).toHaveBeenCalledTimes(1);
    expect(setTwitchChat).not.toHaveBeenCalled();
  });

  it("does not close when the list background is clicked", () => {
    const onRequestClose = jest.fn();
    const { container } = renderSelector({ onRequestClose });
    fireEvent.click(container.querySelector("ul"));
    expect(onRequestClose).not.toHaveBeenCalled();
  });
});
