import {
  cleanTeamNum,
  playoffTypeFromNumber,
  playoffMatchAndSet,
  computePlayoffMatchDetails,
  computePlayoffMatchDetailsFromCounter,
} from "../playoffHelpers";

describe("playoffHelpers", () => {
  describe("cleanTeamNum", () => {
    it("removes asterisks from team numbers", () => {
      expect(cleanTeamNum("254*")).toBe("254");
      expect(cleanTeamNum("1114*")).toBe("1114");
    });

    it("trims whitespace from team numbers", () => {
      expect(cleanTeamNum(" 254 ")).toBe("254");
      expect(cleanTeamNum("  1114  ")).toBe("1114");
    });

    it("handles numeric input", () => {
      expect(cleanTeamNum(254)).toBe("254");
      expect(cleanTeamNum(1114)).toBe("1114");
    });

    it("handles asterisk and whitespace together", () => {
      expect(cleanTeamNum(" 254* ")).toBe("254");
    });

    it("handles team numbers without asterisks or whitespace", () => {
      expect(cleanTeamNum("254")).toBe("254");
      expect(cleanTeamNum("1114")).toBe("1114");
    });
  });

  describe("playoffTypeFromNumber - Standard Bracket (8 alliances)", () => {
    it("identifies quarterfinal matches (1-18)", () => {
      expect(playoffTypeFromNumber(1, false)).toBe("qf");
      expect(playoffTypeFromNumber(9, false)).toBe("qf");
      expect(playoffTypeFromNumber(18, false)).toBe("qf");
    });

    it("identifies semifinal matches (19-24)", () => {
      expect(playoffTypeFromNumber(19, false)).toBe("sf");
      expect(playoffTypeFromNumber(21, false)).toBe("sf");
      expect(playoffTypeFromNumber(24, false)).toBe("sf");
    });

    it("identifies final matches (25+)", () => {
      expect(playoffTypeFromNumber(25, false)).toBe("f");
      expect(playoffTypeFromNumber(26, false)).toBe("f");
      expect(playoffTypeFromNumber(30, false)).toBe("f");
    });
  });

  describe("playoffTypeFromNumber - Standard Bracket (16 alliances)", () => {
    it("identifies octofinal matches (1-24)", () => {
      expect(playoffTypeFromNumber(1, true)).toBe("ef");
      expect(playoffTypeFromNumber(12, true)).toBe("ef");
      expect(playoffTypeFromNumber(24, true)).toBe("ef");
    });

    it("identifies quarterfinal matches (25-36)", () => {
      expect(playoffTypeFromNumber(25, true)).toBe("qf");
      expect(playoffTypeFromNumber(30, true)).toBe("qf");
      expect(playoffTypeFromNumber(36, true)).toBe("qf");
    });

    it("identifies semifinal matches (37-42)", () => {
      expect(playoffTypeFromNumber(37, true)).toBe("sf");
      expect(playoffTypeFromNumber(39, true)).toBe("sf");
      expect(playoffTypeFromNumber(42, true)).toBe("sf");
    });

    it("identifies final matches (43+)", () => {
      expect(playoffTypeFromNumber(43, true)).toBe("f");
      expect(playoffTypeFromNumber(44, true)).toBe("f");
      expect(playoffTypeFromNumber(50, true)).toBe("f");
    });
  });

  describe("playoffMatchAndSet - Standard Bracket (8 alliances)", () => {
    it("returns an array with set and match numbers", () => {
      const result = playoffMatchAndSet(1, false);
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(2);
      expect(typeof result[0]).toBe("number"); // set number
      expect(typeof result[1]).toBe("number"); // match number
    });

    it("returns valid set and match numbers for QF range", () => {
      // Quarterfinals: matches 1-18 should map to sets 1-4, matches 1-3 each (best of 3)
      const [set1, match1] = playoffMatchAndSet(1, false);
      expect(set1).toBeGreaterThanOrEqual(1);
      expect(set1).toBeLessThanOrEqual(4);
      expect(match1).toBeGreaterThanOrEqual(1);
      expect(match1).toBeLessThanOrEqual(3);
    });
  });

  describe("playoffMatchAndSet - Standard Bracket (16 alliances)", () => {
    it("returns an array with set and match numbers for octofinals", () => {
      const result = playoffMatchAndSet(1, true);
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(2);
    });

    it("handles different match numbers correctly", () => {
      // Verify octofinal range (matches 1-24)
      const [set1, match1] = playoffMatchAndSet(1, true);
      expect(set1).toBeGreaterThanOrEqual(1);
      expect(set1).toBeLessThanOrEqual(8);

      // Verify quarterfinal range (matches 25-36)
      const [set25, match25] = playoffMatchAndSet(25, true);
      expect(set25).toBeGreaterThanOrEqual(1);
      expect(set25).toBeLessThanOrEqual(4);
    });
  });

  describe("computePlayoffMatchDetails - Standard Bracket (8 alliances)", () => {
    it("computes correct details for quarterfinal match", () => {
      const result = computePlayoffMatchDetails(1, false, false);
      expect(result).toMatchObject({
        compLevel: "qf",
        setNumber: expect.any(Number),
        matchNumber: expect.any(Number),
        matchKey: expect.stringMatching(/^qf\d+m\d+$/),
      });
      expect(result.setNumber).toBeGreaterThanOrEqual(1);
      expect(result.setNumber).toBeLessThanOrEqual(4);
    });

    it("computes correct details for semifinal match", () => {
      const result = computePlayoffMatchDetails(19, false, false);
      expect(result).toMatchObject({
        compLevel: "sf",
        setNumber: expect.any(Number),
        matchNumber: expect.any(Number),
        matchKey: expect.stringMatching(/^sf\d+m\d+$/),
      });
    });

    it("computes correct details for final match", () => {
      const result = computePlayoffMatchDetails(25, false, false);
      expect(result).toMatchObject({
        compLevel: "f",
        setNumber: 1,
        matchNumber: expect.any(Number),
        matchKey: expect.stringMatching(/^f1m\d+$/),
      });
    });
  });

  describe("computePlayoffMatchDetails - Standard Bracket (16 alliances)", () => {
    it("computes correct details for octofinal match", () => {
      const result = computePlayoffMatchDetails(1, true, false);
      expect(result).toMatchObject({
        compLevel: "ef",
        setNumber: expect.any(Number),
        matchNumber: expect.any(Number),
        matchKey: expect.stringMatching(/^ef\d+m\d+$/),
      });
      expect(result.setNumber).toBeGreaterThanOrEqual(1);
      expect(result.setNumber).toBeLessThanOrEqual(8);
    });

    it("computes correct details for quarterfinal match with octos", () => {
      const result = computePlayoffMatchDetails(25, true, false);
      expect(result).toMatchObject({
        compLevel: "qf",
        setNumber: expect.any(Number),
        matchNumber: expect.any(Number),
        matchKey: expect.stringMatching(/^qf\d+m\d+$/),
      });
    });
  });

  describe("computePlayoffMatchDetails - Double Elimination (8 alliances)", () => {
    it("computes correct details for first round match", () => {
      const result = computePlayoffMatchDetails(1, false, true);
      expect(result).toMatchObject({
        compLevel: "sf",
        setNumber: 1,
        matchNumber: 1,
        matchKey: "sf1m1",
      });
    });

    it("computes correct details for grand finals match", () => {
      const result = computePlayoffMatchDetails(14, false, true);
      expect(result).toMatchObject({
        compLevel: "f",
        setNumber: 1,
        matchNumber: 1,
        matchKey: "f1m1",
      });
    });

    it("computes correct details for grand finals game 2", () => {
      const result = computePlayoffMatchDetails(15, false, true);
      expect(result).toMatchObject({
        compLevel: "f",
        setNumber: 1,
        matchNumber: 2,
        matchKey: "f1m2",
      });
    });
  });

  describe("playoffMatchAndSet - octofinals semifinals and finals", () => {
    it("maps matches 37-42 to semifinal sets", () => {
      expect(playoffMatchAndSet(37, true)).toEqual([1, 1]);
      expect(playoffMatchAndSet(40, true)).toEqual([2, 1]);
      expect(playoffMatchAndSet(42, true)).toEqual([2, 3]);
    });

    it("maps matches after 42 to the finals set", () => {
      expect(playoffMatchAndSet(43, true)).toEqual([1, 1]);
      expect(playoffMatchAndSet(45, true)).toEqual([1, 3]);
    });
  });

  describe("computePlayoffMatchDetails - Double Elimination fallback", () => {
    it("falls back to the standard bracket for numbers outside the mapping", () => {
      expect(computePlayoffMatchDetails(25, false, true)).toEqual({
        compLevel: "f",
        setNumber: 1,
        matchNumber: 1,
        matchKey: "f1m1",
      });
    });
  });

  describe("computePlayoffMatchDetailsFromCounter", () => {
    it("uses the 4-alliance double elimination mapping for counters up to 11", () => {
      expect(computePlayoffMatchDetailsFromCounter(11, false, true)).toEqual({
        compLevel: "f",
        setNumber: 1,
        matchNumber: 6,
        matchKey: "f1m6",
      });
    });

    it("uses the 8-alliance double elimination mapping past 11", () => {
      expect(computePlayoffMatchDetailsFromCounter(12, false, true)).toEqual({
        compLevel: "sf",
        setNumber: 12,
        matchNumber: 1,
        matchKey: "sf12m1",
      });
    });

    it("uses the octofinals mapping when there are octofinals", () => {
      expect(computePlayoffMatchDetailsFromCounter(1, true, false)?.matchKey).toBe(
        "ef1m1"
      );
    });

    it("uses the standard mapping otherwise", () => {
      expect(computePlayoffMatchDetailsFromCounter(13, false, false)?.matchKey).toBe(
        "sf1m1"
      );
    });

    it("returns null for counters outside the mapping", () => {
      expect(computePlayoffMatchDetailsFromCounter(999, false, false)).toBeNull();
      expect(computePlayoffMatchDetailsFromCounter(999, false, true)).toBeNull();
    });
  });
});
