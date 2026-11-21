/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";
import TickerMatch from "../TickerMatch";

const baseMatch = {
  key: "2026casj_qm12",
  event_key: "2026casj",
  c: "qm",
  m: 12,
  s: 1,
  r: -1,
  b: -1,
  w: "",
  rt: ["frc254", "frc1678", "frc604"],
  bt: ["frc971", "frc846", "frc5940"],
};

const renderMatch = (overrides = {}, props = {}) => {
  const utils = render(
    <TickerMatch match={{ ...baseMatch, ...overrides }} {...props} />
  );
  const root = utils.container.firstChild;
  const [label, alliances] = root.children;
  return { ...utils, root, label, alliances };
};

describe("TickerMatch", () => {
  it("renders an unplayed qualification match with team numbers and no scores", () => {
    const { root, label, alliances } = renderMatch();
    expect(label.textContent).toBe("Q12");
    expect(alliances.children[0].textContent).toBe("254, 1678, 604");
    expect(alliances.children[1].textContent).toBe("971, 846, 5940");
    expect(root.style.backgroundColor).toBe("rgb(0, 0, 0)");
    expect(label.style.color).toBe("rgb(255, 255, 255)");
  });

  it("colors a red win and appends the scores", () => {
    const { root, alliances } = renderMatch({ r: 100, b: 50, w: "red" });
    expect(root.style.backgroundColor).toBe("rgb(51, 0, 0)");
    expect(alliances.children[0].textContent).toBe("254, 1678, 604 - 100");
    expect(alliances.children[1].textContent).toBe("971, 846, 5940 - 50");
  });

  it("colors a blue win", () => {
    const { root } = renderMatch({ r: 50, b: 100, w: "blue" });
    expect(root.style.backgroundColor).toBe("rgb(0, 0, 51)");
  });

  it("colors a tie when both scores are set and there is no winner", () => {
    const { root } = renderMatch({ r: 50, b: 50, w: "" });
    expect(root.style.backgroundColor).toBe("rgb(34, 0, 34)");
  });

  it("highlights unplayed matches with a favorite team", () => {
    const { root, label } = renderMatch({}, { hasFavorite: true });
    expect(root.style.backgroundColor).toBe("rgb(230, 193, 0)");
    expect(label.style.color).toBe("rgb(0, 0, 0)");
  });

  it("does not highlight a played match even with a favorite team", () => {
    const { root } = renderMatch(
      { r: 10, b: 20, w: "blue" },
      { hasFavorite: true }
    );
    expect(root.style.backgroundColor).toBe("rgb(0, 0, 51)");
  });

  it("includes the set number for playoff matches", () => {
    expect(renderMatch({ c: "qf", s: 2, m: 3 }).label.textContent).toBe(
      "QF2-3"
    );
    expect(renderMatch({ c: "sf", s: 1, m: 2 }).label.textContent).toBe(
      "SF1-2"
    );
    expect(renderMatch({ c: "f", s: 1, m: 1 }).label.textContent).toBe("F1-1");
    expect(renderMatch({ c: "ef", s: 1, m: 4 }).label.textContent).toBe("EF4");
  });

  it("prefixes the event code in BlueZone mode", () => {
    const { label } = renderMatch({}, { isBlueZone: true });
    expect(label.textContent).toBe("CASJ Q12");
  });
});
