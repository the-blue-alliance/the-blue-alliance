/* @jest-environment jsdom */
import React from "react";
import { render, fireEvent } from "@testing-library/react";
import VideoCellToolbar from "../VideoCellToolbar";

const webcast = {
  key: "2026casj",
  num: 0,
  id: "2026casj-0",
  name: "Silicon Valley Regional",
  type: "youtube",
  channel: "abc",
};

const match = (key, rt, bt) => ({
  key,
  event_key: "2026casj",
  c: "qm",
  m: Number(key.split("qm")[1]),
  s: 1,
  r: -1,
  b: -1,
  w: "",
  rt,
  bt,
});

const matches = [
  match(
    "2026casj_qm1",
    ["frc254", "frc1678", "frc604"],
    ["frc971", "frc846", "frc5940"]
  ),
  match(
    "2026casj_qm2",
    ["frc100", "frc200", "frc300"],
    ["frc400", "frc500", "frc600"]
  ),
  // Schedules posted without teams (2024 wk3 FMS sync issue) are skipped
  match("2026casj_qm3", [], []),
  {
    ...match(
      "2026casj_qm4",
      ["frc1", "frc2", "frc3"],
      ["frc4", "frc5", "frc6"]
    ),
    rt: undefined,
  },
];

const renderToolbar = (props = {}) => {
  const allProps = {
    matches,
    webcast,
    specialWebcastIds: new Set(),
    favoriteTeams: new Set(["frc500"]),
    isBlueZone: false,
    livescoreOn: false,
    layoutId: 3,
    onRequestSwapPosition: jest.fn(),
    onRequestSelectWebcast: jest.fn(),
    onRequestLiveScoresToggle: jest.fn(),
    removeWebcast: jest.fn(),
    style: { bottom: 0 },
    ...props,
  };
  const utils = render(<VideoCellToolbar {...allProps} />);
  return { ...utils, props: allProps };
};

describe("VideoCellToolbar", () => {
  it("links the webcast name to its event page", () => {
    const { getByText, container } = renderToolbar();
    const link = getByText("Silicon Valley Regional").closest("a");
    expect(link.getAttribute("href")).toBe("/event/2026casj");
    expect(link.getAttribute("target")).toBe("_blank");
    expect(container.querySelector(".MuiToolbar-root").style.bottom).toBe(
      "0px"
    );
  });

  it("disables the event link for special webcasts", () => {
    const { getByText } = renderToolbar({
      specialWebcastIds: new Set(["2026casj-0"]),
    });
    const button = getByText("Silicon Valley Regional").closest(
      "[role=button], a, button"
    );
    expect(
      button.getAttribute("aria-disabled") === "true" || button.disabled
    ).toBe(true);
  });

  it("renders a ticker entry for each match with teams, flagging favorites", () => {
    const { getByText, queryByText } = renderToolbar();
    expect(getByText("Q1")).toBeTruthy();
    expect(getByText("Q2")).toBeTruthy();
    expect(queryByText("Q3")).toBeNull();
    expect(queryByText("Q4")).toBeNull();
    // Q2 contains favorite frc500 and is highlighted; Q1 is not
    expect(getByText("Q2").parentNode.style.backgroundColor).toBe(
      "rgb(230, 193, 0)"
    );
    expect(getByText("Q1").parentNode.style.backgroundColor).toBe(
      "rgb(0, 0, 0)"
    );
  });

  it("passes BlueZone mode through to the ticker", () => {
    const { getByText } = renderToolbar({ isBlueZone: true });
    expect(getByText("CASJ Q1")).toBeTruthy();
  });

  it("hides the swap button in single-view layouts", () => {
    expect(renderToolbar({ layoutId: 0 }).queryByLabelText("swap")).toBeNull();
    expect(renderToolbar({ layoutId: 1 }).getByLabelText("swap")).toBeTruthy();
  });

  it("wires the control buttons to their callbacks", () => {
    const { getByLabelText, props } = renderToolbar();
    fireEvent.click(getByLabelText("swap"));
    expect(props.onRequestSwapPosition).toHaveBeenCalledTimes(1);
    fireEvent.click(getByLabelText("change-webcast"));
    expect(props.onRequestSelectWebcast).toHaveBeenCalledTimes(1);
    fireEvent.click(getByLabelText("toggle-livescore"));
    expect(props.onRequestLiveScoresToggle).toHaveBeenCalledTimes(1);
    fireEvent.click(getByLabelText("close-webcast"));
    expect(props.removeWebcast).toHaveBeenCalledWith("2026casj-0");
  });

  it("colors the livescore toggle white while live scores are hidden", () => {
    const { getByLabelText } = renderToolbar({ livescoreOn: false });
    expect(
      getByLabelText("toggle-livescore").querySelector("svg").style.color
    ).toBe("rgb(255, 255, 255)");
  });

  it("colors the livescore toggle green while live scores are shown", () => {
    const { getByLabelText } = renderToolbar({ livescoreOn: true });
    expect(
      getByLabelText("toggle-livescore").querySelector("svg").style.color
    ).toBe("rgb(76, 175, 80)");
  });
});
