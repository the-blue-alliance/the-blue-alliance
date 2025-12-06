import { parseFmsAlliancesFile } from "../fmsAlliancesParser";
import path from "path";
import fs from "fs";
import {
  installMockFileReader,
  restoreFileReader,
} from "./testHelpers/mockFileReader";
import { loadTestFile } from "./testHelpers/fmsReportLoader";

installMockFileReader();

describe("fmsAlliancesParser", () => {
  describe("parseFmsAlliancesFile - Integration Tests with Real FMS Reports", () => {
    let alliancesFile: File;

    beforeAll(() => {
      const filePath = path.join(
        __dirname,
        "..",
        "..",
        "components",
        "eventAlliances",
        "__tests__",
        "data",
        "2025nysu_RankingsReport_Playoffs.xlsx"
      );
      const buffer = fs.readFileSync(filePath);
      alliancesFile = new File(
        [buffer],
        "2025nysu_RankingsReport_Playoffs.xlsx",
        {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
      );
    });

    it("verifies alliance structure from real file", async () => {
      const result = await parseFmsAlliancesFile(alliancesFile);

      expect(result.alliances).toEqual([
        ["frc694", "frc1796", "frc5298"],
        ["frc5736", "frc353", "frc5016"],
        ["frc1493", "frc9016", "frc1880"],
        ["frc2053", "frc2872", "frc379", "frc3624"],
        ["frc287", "frc3419", "frc4467"],
        ["frc9295", "frc4122", "frc1884"],
        ["frc6423", "frc6911", "frc1155"],
        ["frc6593", "frc2601", "frc9642"],
      ]);
      expect(result.allianceCount).toBe(8);
    });

    it("parses 8 alliances from standard FMS report", async () => {
      const result = await parseFmsAlliancesFile(alliancesFile);

      // Should have exactly 8 alliances
      expect(result.alliances).toHaveLength(8);
      expect(result.allianceCount).toBe(8);
    });

    it("parses alliances with varying team counts", async () => {
      const result = await parseFmsAlliancesFile(alliancesFile);

      // Check that alliance 4 has 4 teams while most others have 3
      expect(result.alliances[3]).toHaveLength(4);
      expect(result.alliances[0]).toHaveLength(3);
      expect(result.alliances[1]).toHaveLength(3);
      expect(result.alliances[2]).toHaveLength(3);
    });

    it("formats team numbers correctly with frc prefix", async () => {
      const result = await parseFmsAlliancesFile(alliancesFile);

      // All team keys should start with "frc"
      result.alliances.forEach((alliance) => {
        alliance.forEach((teamKey) => {
          expect(teamKey).toMatch(/^frc\d+$/);
        });
      });
    });

    it("parses captain and backup teams in correct order", async () => {
      const result = await parseFmsAlliancesFile(alliancesFile);

      // Alliance 1: Captain 694, Pick 1: 1796, Pick 2: 5298
      expect(result.alliances[0][0]).toBe("frc694");
      expect(result.alliances[0][1]).toBe("frc1796");
      expect(result.alliances[0][2]).toBe("frc5298");

      // Alliance 4 has 4 teams: Captain 2053, Picks 2872, 379, 3624
      expect(result.alliances[3][0]).toBe("frc2053");
      expect(result.alliances[3][1]).toBe("frc2872");
      expect(result.alliances[3][2]).toBe("frc379");
      expect(result.alliances[3][3]).toBe("frc3624");
    });
  });
});
