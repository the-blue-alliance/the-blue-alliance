/* @jest-environment jsdom */
import React from "react";
import { render, fireEvent, act } from "@testing-library/react";
import SwapPositionDialog from "../SwapPositionDialog";
import { NUM_VIEWS_FOR_LAYOUT } from "../../constants/LayoutConstants";

const originalOffsetWidth = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  "offsetWidth"
);

beforeAll(() => {
  Object.defineProperty(HTMLElement.prototype, "offsetWidth", {
    configurable: true,
    get() {
      return 400;
    },
  });
});

afterAll(() => {
  Object.defineProperty(
    HTMLElement.prototype,
    "offsetWidth",
    originalOffsetWidth
  );
});

const setWindowSize = (width, height) => {
  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    writable: true,
    value: width,
  });
  Object.defineProperty(window, "innerHeight", {
    configurable: true,
    writable: true,
    value: height,
  });
};

const renderDialog = (props = {}) => {
  const allProps = {
    open: true,
    position: 0,
    layoutId: 3,
    swapWebcasts: jest.fn(),
    onRequestClose: jest.fn(),
    ...props,
  };
  const utils = render(<SwapPositionDialog {...allProps} />);
  return { ...utils, props: allProps };
};

const getCells = () =>
  Array.from(document.querySelectorAll(".MuiDialogContent-root > div > div"));

describe("SwapPositionDialog", () => {
  beforeEach(() => {
    setWindowSize(1600, 800);
  });

  it("renders one preview cell per view, disabling the current position", () => {
    const { getByText } = renderDialog({ layoutId: 3, position: 1 });
    expect(getByText("Select a position to swap with")).toBeTruthy();
    const cells = getCells();
    expect(cells).toHaveLength(NUM_VIEWS_FOR_LAYOUT[3]);
    // Current position is disabled (dark grey), others are enabled
    expect(cells[1].style.backgroundColor).toBe("rgb(85, 85, 85)");
    expect(cells[0].style.backgroundColor).toBe("rgb(204, 204, 204)");
    expect(cells[2].style.backgroundColor).toBe("rgb(204, 204, 204)");
  });

  it("sizes the preview to the window's aspect ratio", () => {
    renderDialog();
    const previewContainer = document.querySelector(
      ".MuiDialogContent-root > div"
    );
    // 400px wide container at a 2:1 window aspect ratio
    expect(previewContainer.style.height).toBe("200px");

    act(() => {
      setWindowSize(800, 800);
      window.dispatchEvent(new Event("resize"));
    });
    expect(previewContainer.style.height).toBe("400px");
  });

  it("swaps with the clicked position and closes", () => {
    const { props } = renderDialog({ position: 0 });
    fireEvent.click(getCells()[2]);
    expect(props.swapWebcasts).toHaveBeenCalledWith(0, 2);
    expect(props.onRequestClose).toHaveBeenCalledTimes(1);
  });

  it("closes without swapping from the cancel button", () => {
    const { getByText, props } = renderDialog();
    fireEvent.click(getByText("Cancel"));
    expect(props.swapWebcasts).not.toHaveBeenCalled();
    expect(props.onRequestClose).toHaveBeenCalledTimes(1);
  });

  it("closes when the backdrop is clicked", () => {
    const { props } = renderDialog();
    fireEvent.click(document.querySelector(".MuiBackdrop-root"));
    expect(props.onRequestClose).toHaveBeenCalledTimes(1);
  });

  it("tolerates a missing onRequestClose", () => {
    const { getByText } = renderDialog({ onRequestClose: undefined });
    expect(() => fireEvent.click(getByText("Cancel"))).not.toThrow();
  });

  it("does not size the preview while closed and re-measures when opened", () => {
    const { rerender, props } = renderDialog({ open: false });
    expect(document.querySelector(".MuiDialogContent-root")).toBeNull();

    rerender(<SwapPositionDialog {...props} open />);
    const previewContainer = document.querySelector(
      ".MuiDialogContent-root > div"
    );
    expect(previewContainer.style.height).toBe("200px");
  });

  it("stops listening for resizes after unmount", () => {
    const removeSpy = jest.spyOn(window, "removeEventListener");
    const { unmount } = renderDialog();
    unmount();
    expect(removeSpy).toHaveBeenCalledWith("resize", expect.any(Function));
    removeSpy.mockRestore();
  });
});
