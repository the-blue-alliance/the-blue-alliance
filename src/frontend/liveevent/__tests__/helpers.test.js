import { getCompLevelStr, getMatchSetStr } from "../helpers";

describe("liveevent helpers", () => {
  it.each([
    ["qm", "Quals"],
    ["ef", "Octos"],
    ["qf", "Quarters"],
    ["sf", "Semis"],
    ["f", "Finals"],
  ])("names comp level %s as %s", (c, name) => {
    expect(getCompLevelStr({ c })).toBe(name);
  });

  it("shows only the match number for quals", () => {
    expect(getMatchSetStr({ c: "qm", s: 1, m: 12 })).toBe(12);
  });

  it("shows set and match for playoff matches", () => {
    expect(getMatchSetStr({ c: "sf", s: 2, m: 1 })).toBe("2 - 1");
  });
});
