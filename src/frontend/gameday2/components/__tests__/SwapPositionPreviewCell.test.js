/* @jest-environment jsdom */
import React from "react";
import { render, fireEvent } from "@testing-library/react";
import SwapPositionPreviewCell from "../SwapPositionPreviewCell";

const cellStyle = { width: "50%", height: "100%", position: "absolute" };

describe("SwapPositionPreviewCell", () => {
  it("renders an enabled cell with the layout style and a pointer cursor", () => {
    const { container } = render(
      <SwapPositionPreviewCell style={cellStyle} enabled onClick={() => {}} />
    );
    const cell = container.firstChild;
    expect(cell.style.backgroundColor).toBe("rgb(204, 204, 204)");
    expect(cell.style.cursor).toBe("pointer");
    expect(cell.style.width).toBe("50%");
    expect(cell.style.position).toBe("absolute");
  });

  it("darkens while hovered and restores on mouse out", () => {
    const { container } = render(
      <SwapPositionPreviewCell style={cellStyle} enabled onClick={() => {}} />
    );
    const cell = container.firstChild;
    fireEvent.mouseOver(cell);
    expect(cell.style.backgroundColor).toBe("rgb(170, 170, 170)");
    fireEvent.mouseOut(cell);
    expect(cell.style.backgroundColor).toBe("rgb(204, 204, 204)");
  });

  it("invokes onClick when clicked", () => {
    const onClick = jest.fn();
    const { container } = render(
      <SwapPositionPreviewCell style={cellStyle} enabled onClick={onClick} />
    );
    fireEvent.click(container.firstChild);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("tolerates a missing onClick", () => {
    const { container } = render(
      <SwapPositionPreviewCell style={cellStyle} enabled />
    );
    expect(() => fireEvent.click(container.firstChild)).not.toThrow();
  });

  it("renders a disabled cell in dark grey without a pointer, even when hovered", () => {
    const { container } = render(
      <SwapPositionPreviewCell
        style={cellStyle}
        enabled={false}
        onClick={() => {}}
      />
    );
    const cell = container.firstChild;
    expect(cell.style.backgroundColor).toBe("rgb(85, 85, 85)");
    expect(cell.style.cursor).toBe("");
    fireEvent.mouseOver(cell);
    expect(cell.style.backgroundColor).toBe("rgb(85, 85, 85)");
  });
});
