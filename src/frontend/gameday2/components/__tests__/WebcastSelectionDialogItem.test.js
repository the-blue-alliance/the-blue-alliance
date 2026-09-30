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

describe("Bug #35: WebcastSelectionDialogItem ListItem button prop", () => {
  // Must run before any other test in this file: React only warns about a
  // given unknown DOM attribute once per module registry.
  it("Bug #35: does not pass MUI's removed `button` prop through to the DOM", () => {
    // Wrong today: ListItem lost its `button` prop in MUI v7, so `button` is
    // forwarded to the <li> and React warns about an unknown attribute.
    // Correct: use ListItemButton (or drop the prop); no warning, no attribute.
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
