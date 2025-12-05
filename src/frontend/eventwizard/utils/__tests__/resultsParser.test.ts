import { parseResultsFile } from "../resultsParser";
import fs from "fs";
import path from "path";
import type * as XLSX from "xlsx";

// Mock XLSX
jest.mock("xlsx", () => ({
  read: jest.fn(),
  utils: {
    sheet_to_json: jest.fn(),
  },
}));

const XLSXModule = require("xlsx") as jest.Mocked<typeof XLSX>;

// Mock FileReader
class MockFileReader {
  result?: string;
  onload?: ((event: { target: { result: string } }) => void) | null;

  readAsBinaryString(file: File): void {
    // Simulate async file read
    setTimeout(() => {
      if (this.onload) {
        this.onload({ target: { result: "mock binary data" } });
      }
    }, 0);
  }
}

(global as any).FileReader = MockFileReader;

describe("resultsParser", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("parseResultsFile", () => {
    const mockFile = new File([""], "results.xlsx");

    beforeEach(() => {
      XLSXModule.read.mockReturnValue({
        SheetNames: ["Results"],
        Sheets: {
          Results: {},
        },
      } as any);
    });

    it("parses qualification matches correctly", async () => {
      XLSXModule.utils.sheet_to_json.mockReturnValue([
        {
          Time: "9:00 AM",
          Match: "Qualification 1",
          "Red 1": "254",
          "Red 2": "1114",
          "Red 3": "2056",
          "Blue 1": "118",
          "Blue 2": "1323",
          "Blue 3": "2471",
          "Red Score": "45",
          "Blue Score": "32",
        },
      ] as any);

      const results = await parseResultsFile(
        mockFile,
        "2024casj",
        false,
        false
      );

      expect(results).toHaveLength(1);
      expect(results[0]).toMatchObject({
        comp_level: "qm",
        set_number: 1,
        match_number: 1,
        alliances: {
          red: {
            teams: ["frc254", "frc1114", "frc2056"],
            score: 45,
          },
          blue: {
            teams: ["frc118", "frc1323", "frc2471"],
            score: 32,
          },
        },
        time_string: "9:00 AM",
        tbaMatchKey: "2024casj_qm1",
      });
    });

    it("parses playoff matches with standard 8-alliance bracket", async () => {
      XLSXModule.utils.sheet_to_json.mockReturnValue([
        {
          Time: "2:00 PM",
          Match: "Quarterfinal 1-1",
          "Red 1": "254",
          "Red 2": "1114",
          "Red 3": "2056",
          "Blue 1": "118",
          "Blue 2": "1323",
          "Blue 3": "2471",
          "Red Score": "120",
          "Blue Score": "110",
        },
      ] as any);

      const results = await parseResultsFile(
        mockFile,
        "2024casj",
        false,
        false
      );

      expect(results).toHaveLength(1);
      expect(results[0]).toMatchObject({
        comp_level: "qf",
        set_number: 1,
        match_number: 1,
        tbaMatchKey: "2024casj_qf1m1",
      });
    });

    it("parses playoff matches with octofinals (16 alliances)", async () => {
      XLSXModule.utils.sheet_to_json.mockReturnValue([
        {
          Time: "1:00 PM",
          Match: "Octofinal 1",
          "Red 1": "254",
          "Red 2": "1114",
          "Red 3": "2056",
          "Blue 1": "118",
          "Blue 2": "1323",
          "Blue 3": "2471",
          "Red Score": "100",
          "Blue Score": "95",
        },
      ] as any);

      const results = await parseResultsFile(mockFile, "2024casj", true, false);

      expect(results).toHaveLength(1);
      expect(results[0]).toMatchObject({
        comp_level: "ef",
        set_number: 1,
        match_number: 1,
        tbaMatchKey: "2024casj_ef1m1",
      });
    });

    it("parses playoff matches with double elimination (8 alliances)", async () => {
      XLSXModule.utils.sheet_to_json.mockReturnValue([
        {
          Time: "3:00 PM",
          Match: "Match 1 (R1) (#1)",
          "Red 1": "254",
          "Red 2": "1114",
          "Red 3": "2056",
          "Blue 1": "118",
          "Blue 2": "1323",
          "Blue 3": "2471",
          "Red Score": "130",
          "Blue Score": "125",
        },
      ] as any);

      const results = await parseResultsFile(mockFile, "2024casj", false, true);

      expect(results).toHaveLength(1);
      expect(results[0]).toMatchObject({
        comp_level: "sf",
        set_number: 1,
        match_number: 1,
        tbaMatchKey: "2024casj_sf1m1",
      });
    });

    it("skips rows without Time field", async () => {
      XLSXModule.utils.sheet_to_json.mockReturnValue([
        {
          Time: "",
          Match: "Invalid",
          "Red 1": "254",
          "Red 2": "1114",
          "Red 3": "2056",
          "Blue 1": "118",
          "Blue 2": "1323",
          "Blue 3": "2471",
          "Red Score": "45",
          "Blue Score": "32",
        },
        {
          Time: "9:00 AM",
          Match: "Qualification 1",
          "Red 1": "254",
          "Red 2": "1114",
          "Red 3": "2056",
          "Blue 1": "118",
          "Blue 2": "1323",
          "Blue 3": "2471",
          "Red Score": "45",
          "Blue Score": "32",
        },
      ] as any);

      const results = await parseResultsFile(
        mockFile,
        "2024casj",
        false,
        false
      );

      expect(results).toHaveLength(1);
      expect(results[0].match_number).toBe(1);
    });

    it("cleans team numbers with asterisks", async () => {
      XLSXModule.utils.sheet_to_json.mockReturnValue([
        {
          Time: "9:00 AM",
          Match: "Qualification 1",
          "Red 1": "254*",
          "Red 2": " 1114 ",
          "Red 3": "2056*",
          "Blue 1": "118",
          "Blue 2": " 1323* ",
          "Blue 3": "2471",
          "Red Score": "45",
          "Blue Score": "32",
        },
      ] as any);

      const results = await parseResultsFile(
        mockFile,
        "2024casj",
        false,
        false
      );

      expect(results).toHaveLength(1);
      expect(results[0].alliances.red.teams).toEqual([
        "frc254",
        "frc1114",
        "frc2056",
      ]);
      expect(results[0].alliances.blue.teams).toEqual([
        "frc118",
        "frc1323",
        "frc2471",
      ]);
    });

    it("handles missing scores as 0", async () => {
      XLSXModule.utils.sheet_to_json.mockReturnValue([
        {
          Time: "9:00 AM",
          Match: "Qualification 1",
          "Red 1": "254",
          "Red 2": "1114",
          "Red 3": "2056",
          "Blue 1": "118",
          "Blue 2": "1323",
          "Blue 3": "2471",
          "Red Score": "",
          "Blue Score": "",
        },
      ] as any);

      const results = await parseResultsFile(
        mockFile,
        "2024casj",
        false,
        false
      );

      expect(results).toHaveLength(1);
      expect(results[0].alliances.red.score).toBe(0);
      expect(results[0].alliances.blue.score).toBe(0);
    });

    it("includes display-only fields for preview", async () => {
      XLSXModule.utils.sheet_to_json.mockReturnValue([
        {
          Time: "9:00 AM",
          Match: "Qualification 1",
          "Red 1": "254",
          "Red 2": "1114",
          "Red 3": "2056",
          "Blue 1": "118",
          "Blue 2": "1323",
          "Blue 3": "2471",
          "Red Score": "45",
          "Blue Score": "32",
        },
      ] as any);

      const results = await parseResultsFile(
        mockFile,
        "2024casj",
        false,
        false
      );

      expect(results[0]).toHaveProperty("tbaMatchKey", "2024casj_qm1");
      expect(results[0]).toHaveProperty("description", "Qualification 1");
      expect(results[0]).toHaveProperty("timeString", "9:00 AM");
      expect(results[0]).toHaveProperty("rawRedTeams", ["254", "1114", "2056"]);
      expect(results[0]).toHaveProperty("rawBlueTeams", [
        "118",
        "1323",
        "2471",
      ]);
    });

    it("handles file read errors", async () => {
      XLSXModule.read.mockImplementation(() => {
        throw new Error("Invalid file format");
      });

      await expect(
        parseResultsFile(mockFile, "2024casj", false, false)
      ).rejects.toThrow("Invalid file format");
    });
  });

  describe("Integration Tests with Real FMS Reports", () => {
    // Unmock XLSX for integration tests
    beforeAll(() => {
      jest.unmock("xlsx");
    });

    afterAll(() => {
      jest.mock("xlsx");
    });

    // Mock FileReader for Node.js environment
    class RealFileReader {
      result?: string;
      onload?: ((event: { target: RealFileReader }) => void) | null;

      readAsBinaryString(blob: Blob | Buffer): void {
        const reader = this;
        const arrayBuffer = (blob as any).arrayBuffer
          ? (blob as any).arrayBuffer()
          : Promise.resolve(blob);

        arrayBuffer.then((buffer: ArrayBuffer | Buffer) => {
          if (buffer instanceof ArrayBuffer) {
            reader.result = Buffer.from(buffer).toString("binary");
          } else if (Buffer.isBuffer(buffer)) {
            reader.result = buffer.toString("binary");
          } else {
            reader.result = buffer as any;
          }

          if (reader.onload) {
            reader.onload({ target: reader });
          }
        });
      }
    }

    describe("Qualification Matches", () => {
      let qualsFile: File;
      const realXLSX = jest.requireActual("xlsx");

      beforeAll(() => {
        (global as any).FileReader = RealFileReader;
        Object.assign(XLSXModule, realXLSX);

        const filePath = path.join(
          __dirname,
          "..",
          "..",
          "components",
          "eventMatchResultsTab",
          "__tests__",
          "data",
          "2025nysu_MatchResultsReport_Quals.xlsx"
        );
        const buffer = fs.readFileSync(filePath);
        qualsFile = new File(
          [buffer],
          "2025nysu_MatchResultsReport_Quals.xlsx",
          {
            type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          }
        );
      });

      afterAll(() => {
        (global as any).FileReader = MockFileReader;
      });

      it("parses all qualification matches from real FMS report", async () => {
        const matches = await parseResultsFile(
          qualsFile,
          "2025nysu",
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
        const matches = await parseResultsFile(
          qualsFile,
          "2025nysu",
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
        const matches = await parseResultsFile(
          qualsFile,
          "2025nysu",
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
        const matches = await parseResultsFile(
          qualsFile,
          "2025nysu",
          false,
          false
        );

        const firstMatch = matches[0];

        // Should have time and description fields
        expect(firstMatch.timeString).toBeDefined();
        expect(firstMatch.description).toBeDefined();
        expect(firstMatch.description).toBe("Qualification 1");
      });

      it("parses scores correctly from qual matches", async () => {
        const matches = await parseResultsFile(
          qualsFile,
          "2025nysu",
          false,
          false
        );

        const firstMatch = matches[0];

        // Should have score objects
        expect(firstMatch.alliances.red.score).toBeDefined();
        expect(firstMatch.alliances.blue.score).toBeDefined();

        // Scores should be numbers
        expect(typeof firstMatch.alliances.red.score).toBe("number");
        expect(typeof firstMatch.alliances.blue.score).toBe("number");
      });
    });

    describe("Playoff Matches - Double Elimination", () => {
      let playoffsFile: File;
      const realXLSX = jest.requireActual("xlsx");

      beforeAll(() => {
        (global as any).FileReader = RealFileReader;
        Object.assign(XLSXModule, realXLSX);

        const filePath = path.join(
          __dirname,
          "..",
          "..",
          "components",
          "eventMatchResultsTab",
          "__tests__",
          "data",
          "2025nysu_MatchResultsReport_Playoffs.xlsx"
        );
        const buffer = fs.readFileSync(filePath);
        playoffsFile = new File(
          [buffer],
          "2025nysu_MatchResultsReport_Playoffs.xlsx",
          {
            type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          }
        );
      });

      afterAll(() => {
        (global as any).FileReader = MockFileReader;
      });

      it("parses all playoff matches from real FMS report", async () => {
        const matches = await parseResultsFile(
          playoffsFile,
          "2025nysu",
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
        const matches = await parseResultsFile(
          playoffsFile,
          "2025nysu",
          false,
          true
        );

        // Match 1 should be sf1m1 per DOUBLE_ELIM_MAPPING
        const match1 = matches[0];
        expect(match1.comp_level).toBe("sf");
        expect(match1.set_number).toBe(1);
        expect(match1.match_number).toBe(1);
        expect(match1.tbaMatchKey).toBe("2025nysu_sf1m1");

        // Match 5 should be sf5m1 per DOUBLE_ELIM_MAPPING
        const match5 = matches[4];
        expect(match5.comp_level).toBe("sf");
        expect(match5.set_number).toBe(5);
        expect(match5.match_number).toBe(1);
        expect(match5.tbaMatchKey).toBe("2025nysu_sf5m1");

        // Finals should be f1m1 and f1m2
        const finals = matches.filter((m) => m.comp_level === "f");
        expect(finals.length).toBeGreaterThanOrEqual(2);
        expect(finals[0].set_number).toBe(1);
        expect(finals[0].match_number).toBe(1);
        expect(finals[0].tbaMatchKey).toBe("2025nysu_f1m1");
        expect(finals[1].set_number).toBe(1);
        expect(finals[1].match_number).toBe(2);
        expect(finals[1].tbaMatchKey).toBe("2025nysu_f1m2");
      });

      it("parses team alliances correctly from playoff matches", async () => {
        const matches = await parseResultsFile(
          playoffsFile,
          "2025nysu",
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

      it("parses scores correctly from playoff matches", async () => {
        const matches = await parseResultsFile(
          playoffsFile,
          "2025nysu",
          false,
          true
        );

        matches.forEach((match) => {
          // Should have score objects
          expect(match.alliances.red.score).toBeDefined();
          expect(match.alliances.blue.score).toBeDefined();

          // Scores should be numbers
          expect(typeof match.alliances.red.score).toBe("number");
          expect(typeof match.alliances.blue.score).toBe("number");
        });
      });

      it("includes display fields for preview", async () => {
        const matches = await parseResultsFile(
          playoffsFile,
          "2025nysu",
          false,
          true
        );

        const firstMatch = matches[0];

        // Should have display-only fields
        expect(firstMatch.tbaMatchKey).toBeDefined();
        expect(firstMatch.description).toBeDefined();
        expect(firstMatch.timeString).toBeDefined();
        expect(firstMatch.rawRedTeams).toBeDefined();
        expect(firstMatch.rawBlueTeams).toBeDefined();

        // Raw teams should be arrays of team numbers (without frc prefix)
        expect(Array.isArray(firstMatch.rawRedTeams)).toBe(true);
        expect(Array.isArray(firstMatch.rawBlueTeams)).toBe(true);
        expect(firstMatch.rawRedTeams).toHaveLength(3);
        expect(firstMatch.rawBlueTeams).toHaveLength(3);
      });

      it("skips non-match rows like awards breaks", async () => {
        const matches = await parseResultsFile(
          playoffsFile,
          "2025nysu",
          false,
          true
        );

        // Should not include "Awards Break" rows or other non-match entries
        matches.forEach((match) => {
          expect(match.description).not.toContain("Awards Break");
          expect(match.alliances).toBeDefined();
          expect(match.comp_level).toBeDefined();
        });
      });
    });
  });
});
