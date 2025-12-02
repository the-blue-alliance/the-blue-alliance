import { parseScheduleFile } from "../scheduleParser";
import fs from "fs";
import path from "path";

// Mock FileReader for Node.js environment
class MockFileReader {
  readAsBinaryString(blob) {
    // Convert blob to buffer, then to binary string
    const reader = this;
    const arrayBuffer = blob.arrayBuffer
      ? blob.arrayBuffer()
      : Promise.resolve(blob);

    arrayBuffer.then((buffer) => {
      if (buffer instanceof ArrayBuffer) {
        reader.result = Buffer.from(buffer).toString("binary");
      } else if (Buffer.isBuffer(buffer)) {
        reader.result = buffer.toString("binary");
      } else {
        reader.result = buffer;
      }

      if (reader.onload) {
        reader.onload({ target: reader });
      }
    });
  }
}

global.FileReader = MockFileReader;

describe("scheduleParser", () => {
  describe("parseScheduleFile - Integration Tests with Real FMS Reports", () => {
    describe("Qualification Matches", () => {
      let qualsFile;

      beforeAll(() => {
        const filePath = path.join(
          __dirname,
          "..",
          "..",
          "components",
          "eventScheduleTab",
          "__tests__",
          "data",
          "2025nysu_ScheduleReport_Quals.xlsx"
        );
        const buffer = fs.readFileSync(filePath);
        qualsFile = new File([buffer], "2025nysu_ScheduleReport_Quals.xlsx", {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        });
      });

      it("parses all qualification matches from real FMS report", async () => {
        const matches = await parseScheduleFile(
          qualsFile,
          "2025nysu",
          "all",
          false,
          false
        );

        // Should have parsed qualification matches (file has 78 qual matches)
        expect(matches.length).toBeGreaterThan(70);
        expect(matches.length).toBeLessThan(85);

        // All should be qualification matches
        matches.forEach((match) => {
          expect(match.comp_level).toBe("qm");
        });
      });

      it("generates correct TBA match keys for qualification matches", async () => {
        const matches = await parseScheduleFile(
          qualsFile,
          "2025nysu",
          "all",
          false,
          false
        );

        // Check first match
        expect(matches[0].tbaMatchKey).toBe("2025nysu_qm1");
        expect(matches[0].match_number).toBe(1);

        // Check last match
        const lastMatch = matches[matches.length - 1];
        expect(lastMatch.tbaMatchKey).toMatch(/^2025nysu_qm\d+$/);
        expect(lastMatch.match_number).toBe(matches.length);
      });

      it("parses team alliances correctly from qual matches", async () => {
        const matches = await parseScheduleFile(
          qualsFile,
          "2025nysu",
          "all",
          false,
          false
        );

        const firstMatch = matches[0];

        // Should have 3 teams per alliance
        expect(firstMatch.alliances.blue.teams).toHaveLength(3);
        expect(firstMatch.alliances.red.teams).toHaveLength(3);

        // Team keys should be in correct format
        firstMatch.alliances.blue.teams.forEach((key) => {
          expect(key).toMatch(/^frc\d+$/);
        });
        firstMatch.alliances.red.teams.forEach((key) => {
          expect(key).toMatch(/^frc\d+$/);
        });

        // Verify specific teams from the fixture (first match)
        expect(firstMatch.alliances.blue.teams).toEqual([
          "frc6463",
          "frc1155",
          "frc353",
        ]);
        expect(firstMatch.alliances.red.teams).toEqual([
          "frc7668",
          "frc10152",
          "frc5736",
        ]);
      });

      it("includes time and description fields", async () => {
        const matches = await parseScheduleFile(
          qualsFile,
          "2025nysu",
          "all",
          false,
          false
        );

        const firstMatch = matches[0];

        // Should have time and description fields
        expect(firstMatch.timeString).toBeDefined();
        expect(firstMatch.description).toBeDefined();
        expect(firstMatch.description).toBe("Qualification 1");
      });
    });

    describe("Playoff Matches - Double Elimination", () => {
      let playoffsFile;

      beforeAll(() => {
        const filePath = path.join(
          __dirname,
          "..",
          "..",
          "components",
          "eventScheduleTab",
          "__tests__",
          "data",
          "2025nysu_ScheduleReport_Playoffs.xlsx"
        );
        const buffer = fs.readFileSync(filePath);
        playoffsFile = new File(
          [buffer],
          "2025nysu_ScheduleReport_Playoffs.xlsx",
          {
            type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          }
        );
      });

      it("parses all playoff matches from real FMS report", async () => {
        const matches = await parseScheduleFile(
          playoffsFile,
          "2025nysu",
          "all",
          false,
          true
        );

        // Playoff file has matches 1-15 (13 semis + 2 finals, with awards break)
        expect(matches.length).toBeGreaterThanOrEqual(13);
        expect(matches.length).toBeLessThanOrEqual(15);

        // Should have both semifinals and finals
        const compLevels = new Set(matches.map((m) => m.comp_level));
        expect(compLevels.has("sf")).toBe(true);
        expect(compLevels.has("f")).toBe(true);
      });

      it("uses double elimination mapping for playoff matches", async () => {
        const matches = await parseScheduleFile(
          playoffsFile,
          "2025nysu",
          "all",
          false,
          true
        );

        // Match 1 should be sf1m1 per DOUBLE_ELIM_MAPPING
        const match1 = matches.find(
          (m) => m.description === "Match 1 (R1) (#1)"
        );
        expect(match1).toBeDefined();
        expect(match1.comp_level).toBe("sf");
        expect(match1.set_number).toBe(1);
        expect(match1.match_number).toBe(1);
        expect(match1.tbaMatchKey).toBe("2025nysu_sf1m1");

        // Match 5 should be sf5m1 per DOUBLE_ELIM_MAPPING
        const match5 = matches.find(
          (m) => m.description === "Match 5 (R2) (#5)"
        );
        expect(match5).toBeDefined();
        expect(match5.comp_level).toBe("sf");
        expect(match5.set_number).toBe(5);
        expect(match5.match_number).toBe(1);
        expect(match5.tbaMatchKey).toBe("2025nysu_sf5m1");

        // Match 14 (Final 1) should be f1m1
        const final1 = matches.find((m) => m.description === "Final 1 (#14)");
        expect(final1).toBeDefined();
        expect(final1.comp_level).toBe("f");
        expect(final1.set_number).toBe(1);
        expect(final1.match_number).toBe(1);
        expect(final1.tbaMatchKey).toBe("2025nysu_f1m1");

        // Match 15 (Final 2) should be f1m2
        const final2 = matches.find((m) => m.description === "Final 2 (#15)");
        expect(final2).toBeDefined();
        expect(final2.comp_level).toBe("f");
        expect(final2.set_number).toBe(1);
        expect(final2.match_number).toBe(2);
        expect(final2.tbaMatchKey).toBe("2025nysu_f1m2");
      });

      it("filters playoff matches by competition level", async () => {
        // Filter for semifinals only
        const sfMatches = await parseScheduleFile(
          playoffsFile,
          "2025nysu",
          "sf",
          false,
          true
        );

        sfMatches.forEach((match) => {
          expect(match.comp_level).toBe("sf");
        });

        // Should have 13 semifinal matches in double elim bracket
        expect(sfMatches.length).toBe(13);

        // Filter for finals only
        const finalMatches = await parseScheduleFile(
          playoffsFile,
          "2025nysu",
          "f",
          false,
          true
        );

        finalMatches.forEach((match) => {
          expect(match.comp_level).toBe("f");
        });

        // Should have 2 finals matches
        expect(finalMatches.length).toBe(2);
      });

      it("parses team alliances correctly from playoff matches", async () => {
        const matches = await parseScheduleFile(
          playoffsFile,
          "2025nysu",
          "all",
          false,
          true
        );

        const firstMatch = matches[0];

        // Should have 3 teams per alliance
        expect(firstMatch.alliances.blue.teams).toHaveLength(3);
        expect(firstMatch.alliances.red.teams).toHaveLength(3);

        // Verify specific teams from fixture (Match 1)
        expect(firstMatch.alliances.blue.teams).toEqual([
          "frc6593",
          "frc9642",
          "frc2601",
        ]);
        expect(firstMatch.alliances.red.teams).toEqual([
          "frc694",
          "frc5298",
          "frc1796",
        ]);
      });

      it("extracts match numbers from description parentheses", async () => {
        const matches = await parseScheduleFile(
          playoffsFile,
          "2025nysu",
          "all",
          false,
          true
        );

        // Check that match numbers were extracted correctly from (#n) format
        const match1 = matches.find((m) => m.description?.includes("(#1)"));
        expect(match1).toBeDefined();
        expect(match1.rawMatchNumber).toBe(1);

        const match9 = matches.find((m) => m.description?.includes("(#9)"));
        expect(match9).toBeDefined();
        expect(match9.comp_level).toBe("sf");
        expect(match9.rawMatchNumber).toBe(9);

        const match15 = matches.find((m) => m.description?.includes("(#15)"));
        expect(match15).toBeDefined();
        expect(match15.comp_level).toBe("f");
        expect(match15.rawMatchNumber).toBe(15);
      });
    });

    describe("Edge Cases and Error Handling", () => {
      it("handles empty rows gracefully", async () => {
        const filePath = path.join(
          __dirname,
          "..",
          "..",
          "components",
          "eventScheduleTab",
          "__tests__",
          "data",
          "2025nysu_ScheduleReport_Quals.xlsx"
        );
        const buffer = fs.readFileSync(filePath);
        const file = new File([buffer], "2025nysu_ScheduleReport_Quals.xlsx", {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        });

        const matches = await parseScheduleFile(
          file,
          "2025nysu",
          "all",
          false,
          false
        );

        // Should successfully parse despite empty rows in Excel file
        expect(matches.length).toBeGreaterThan(0);
      });

      it("skips non-match rows like awards breaks", async () => {
        const filePath = path.join(
          __dirname,
          "..",
          "..",
          "components",
          "eventScheduleTab",
          "__tests__",
          "data",
          "2025nysu_ScheduleReport_Playoffs.xlsx"
        );
        const buffer = fs.readFileSync(filePath);
        const file = new File(
          [buffer],
          "2025nysu_ScheduleReport_Playoffs.xlsx",
          {
            type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          }
        );

        const matches = await parseScheduleFile(
          file,
          "2025nysu",
          "all",
          false,
          true
        );

        // Should not include "Awards Break" rows
        matches.forEach((match) => {
          expect(match.description).not.toContain("Awards Break");
        });
      });
    });
  });
});
