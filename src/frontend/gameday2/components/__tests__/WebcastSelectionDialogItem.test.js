/* @jest-environment jsdom */
import React from "react";
import { format } from "util";
import { render, fireEvent } from "@testing-library/react";
import WebcastSelectionDialogItem from "../WebcastSelectionDialogItem";

const webcast = {
  key: "2026casj",
  num: 0,
  id: "2026casj-0",
  name: "Silicon Valley Regional",
  type: "youtube",
  channel: "abc",
};

describe("WebcastSelectionDialogItem ListItem button prop", () => {
  // Runs first: React warns about a given unknown DOM attribute only once per module registry.
  it("does not pass MUI's removed `button` prop through to the DOM", () => {
    // MUI v7 ListItem has no `button` prop; React warns if it reaches the DOM.
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    try {
      render(
        <WebcastSelectionDialogItem
          webcast={webcast}
          webcastSelected={() => {}}
          secondaryText="Qualification 12"
        />
      );
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

describe("WebcastSelectionDialogItem", () => {
  it("renders the webcast name, secondary text and both icons", () => {
    const { getByText, getByTestId } = render(
      <WebcastSelectionDialogItem
        webcast={webcast}
        webcastSelected={() => {}}
        secondaryText="Qualification 12"
        leftIcon={<span data-testid="left" />}
        rightIcon={<span data-testid="right" />}
      />
    );
    expect(getByText("Silicon Valley Regional")).toBeTruthy();
    expect(getByText("Qualification 12")).toBeTruthy();
    expect(getByTestId("left")).toBeTruthy();
    expect(getByTestId("right")).toBeTruthy();
  });

  it("omits the icon slots when no icons are given", () => {
    const { container } = render(
      <WebcastSelectionDialogItem
        webcast={webcast}
        webcastSelected={() => {}}
      />
    );
    expect(container.querySelector(".MuiListItemIcon-root")).toBeNull();
    expect(
      container.querySelector(".MuiListItemSecondaryAction-root")
    ).toBeNull();
  });

  it("reports the webcast id when clicked", () => {
    const webcastSelected = jest.fn();
    const { getByText } = render(
      <WebcastSelectionDialogItem
        webcast={webcast}
        webcastSelected={webcastSelected}
      />
    );
    fireEvent.click(getByText("Silicon Valley Regional"));
    expect(webcastSelected).toHaveBeenCalledWith("2026casj-0");
  });
});
