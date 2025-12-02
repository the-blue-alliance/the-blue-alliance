import {
  DOUBLE_ELIM_MAPPING,
  DOUBLE_ELIM_4_MAPPING,
  ELIM_MAPPING,
  OCTO_ELIM_MAPPING,
} from "../playoffMappings";

describe("playoffMappings", () => {
  describe("DOUBLE_ELIM_MAPPING (8 alliances)", () => {
    it("maps match 1 to sf1m1", () => {
      expect(DOUBLE_ELIM_MAPPING[1]).toEqual(["sf", 1, 1]);
    });

    it("maps match 5 to sf5m1 (round 2)", () => {
      expect(DOUBLE_ELIM_MAPPING[5]).toEqual(["sf", 5, 1]);
    });

    it("maps match 14 to f1m1 (grand finals match 1)", () => {
      expect(DOUBLE_ELIM_MAPPING[14]).toEqual(["f", 1, 1]);
    });

    it("maps match 15 to f1m2 (grand finals match 2)", () => {
      expect(DOUBLE_ELIM_MAPPING[15]).toEqual(["f", 1, 2]);
    });

    it("maps match 19 to f1m6 (grand finals match 6)", () => {
      expect(DOUBLE_ELIM_MAPPING[19]).toEqual(["f", 1, 6]);
    });

    it("contains 19 mappings for 8-alliance double elim", () => {
      expect(Object.keys(DOUBLE_ELIM_MAPPING).length).toBe(19);
    });

    it("has sequential match numbers from 1 to 19", () => {
      for (let i = 1; i <= 19; i++) {
        expect(DOUBLE_ELIM_MAPPING[i]).toBeDefined();
      }
    });
  });

  describe("DOUBLE_ELIM_4_MAPPING (4 alliances)", () => {
    it("maps match 1 to sf1m1", () => {
      expect(DOUBLE_ELIM_4_MAPPING[1]).toEqual(["sf", 1, 1]);
    });

    it("maps match 6 to f1m1 (grand finals match 1)", () => {
      expect(DOUBLE_ELIM_4_MAPPING[6]).toEqual(["f", 1, 1]);
    });

    it("maps match 7 to f1m2 (grand finals match 2)", () => {
      expect(DOUBLE_ELIM_4_MAPPING[7]).toEqual(["f", 1, 2]);
    });

    it("maps match 11 to f1m6 (grand finals match 6)", () => {
      expect(DOUBLE_ELIM_4_MAPPING[11]).toEqual(["f", 1, 6]);
    });

    it("contains 11 mappings for 4-alliance double elim", () => {
      expect(Object.keys(DOUBLE_ELIM_4_MAPPING).length).toBe(11);
    });

    it("has sequential match numbers from 1 to 11", () => {
      for (let i = 1; i <= 11; i++) {
        expect(DOUBLE_ELIM_4_MAPPING[i]).toBeDefined();
      }
    });
  });

  describe("ELIM_MAPPING (8 alliances standard bracket)", () => {
    it("maps match 1 to qf1m1 (quarterfinal)", () => {
      expect(ELIM_MAPPING[1]).toEqual(["qf", 1, 1]);
    });

    it("maps match 13 to sf1m1 (semifinal)", () => {
      expect(ELIM_MAPPING[13]).toEqual(["sf", 1, 1]);
    });

    it("maps match 19 to f1m1 (final)", () => {
      expect(ELIM_MAPPING[19]).toEqual(["f", 1, 1]);
    });

    it("contains 21 mappings for standard 8-alliance bracket", () => {
      expect(Object.keys(ELIM_MAPPING).length).toBe(21);
    });

    it("has sequential match numbers from 1 to 21", () => {
      for (let i = 1; i <= 21; i++) {
        expect(ELIM_MAPPING[i]).toBeDefined();
      }
    });

    it("has 4 quarterfinal sets (12 matches)", () => {
      const qfMatches = Object.values(ELIM_MAPPING).filter(
        ([level]) => level === "qf"
      );
      expect(qfMatches.length).toBe(12);
    });

    it("has 2 semifinal sets (6 matches)", () => {
      const sfMatches = Object.values(ELIM_MAPPING).filter(
        ([level]) => level === "sf"
      );
      expect(sfMatches.length).toBe(6);
    });

    it("has 1 final set (3 matches)", () => {
      const fMatches = Object.values(ELIM_MAPPING).filter(
        ([level]) => level === "f"
      );
      expect(fMatches.length).toBe(3);
    });
  });

  describe("OCTO_ELIM_MAPPING (16 alliances standard bracket)", () => {
    it("maps match 1 to ef1m1 (octofinal)", () => {
      expect(OCTO_ELIM_MAPPING[1]).toEqual(["ef", 1, 1]);
    });

    it("maps match 25 to qf1m1 (quarterfinal)", () => {
      expect(OCTO_ELIM_MAPPING[25]).toEqual(["qf", 1, 1]);
    });

    it("maps match 37 to sf1m1 (semifinal)", () => {
      expect(OCTO_ELIM_MAPPING[37]).toEqual(["sf", 1, 1]);
    });

    it("maps match 43 to f1m1 (final)", () => {
      expect(OCTO_ELIM_MAPPING[43]).toEqual(["f", 1, 1]);
    });

    it("contains 45 mappings for 16-alliance bracket", () => {
      expect(Object.keys(OCTO_ELIM_MAPPING).length).toBe(45);
    });

    it("has sequential match numbers from 1 to 45", () => {
      for (let i = 1; i <= 45; i++) {
        expect(OCTO_ELIM_MAPPING[i]).toBeDefined();
      }
    });

    it("has 8 octofinal sets (24 matches)", () => {
      const efMatches = Object.values(OCTO_ELIM_MAPPING).filter(
        ([level]) => level === "ef"
      );
      expect(efMatches.length).toBe(24);
    });

    it("has 4 quarterfinal sets (12 matches)", () => {
      const qfMatches = Object.values(OCTO_ELIM_MAPPING).filter(
        ([level]) => level === "qf"
      );
      expect(qfMatches.length).toBe(12);
    });

    it("has 2 semifinal sets (6 matches)", () => {
      const sfMatches = Object.values(OCTO_ELIM_MAPPING).filter(
        ([level]) => level === "sf"
      );
      expect(sfMatches.length).toBe(6);
    });

    it("has 1 final set (3 matches)", () => {
      const fMatches = Object.values(OCTO_ELIM_MAPPING).filter(
        ([level]) => level === "f"
      );
      expect(fMatches.length).toBe(3);
    });
  });

  describe("Mapping consistency", () => {
    it("all mappings use valid competition levels", () => {
      const validLevels = ["ef", "qf", "sf", "f"];
      const allMappings = [
        ...Object.values(DOUBLE_ELIM_MAPPING),
        ...Object.values(DOUBLE_ELIM_4_MAPPING),
        ...Object.values(ELIM_MAPPING),
        ...Object.values(OCTO_ELIM_MAPPING),
      ];

      allMappings.forEach(([level]) => {
        expect(validLevels).toContain(level);
      });
    });

    it("all mappings have valid set numbers (positive integers)", () => {
      const allMappings = [
        ...Object.values(DOUBLE_ELIM_MAPPING),
        ...Object.values(DOUBLE_ELIM_4_MAPPING),
        ...Object.values(ELIM_MAPPING),
        ...Object.values(OCTO_ELIM_MAPPING),
      ];

      allMappings.forEach(([, setNumber]) => {
        expect(setNumber).toBeGreaterThan(0);
        expect(Number.isInteger(setNumber)).toBe(true);
      });
    });

    it("all mappings have valid match numbers (positive integers)", () => {
      const allMappings = [
        ...Object.values(DOUBLE_ELIM_MAPPING),
        ...Object.values(DOUBLE_ELIM_4_MAPPING),
        ...Object.values(ELIM_MAPPING),
        ...Object.values(OCTO_ELIM_MAPPING),
      ];

      allMappings.forEach(([, , matchNumber]) => {
        expect(matchNumber).toBeGreaterThan(0);
        expect(Number.isInteger(matchNumber)).toBe(true);
      });
    });
  });
});
