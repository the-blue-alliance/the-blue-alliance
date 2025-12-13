import XLSX from "xlsx";

export interface FmsAlliancesResult {
  alliances: string[][];
  allianceCount: number;
}

/**
 * Parse FMS Alliance Selection Excel file
 * This parser is year-agnostic and extracts alliance data from the FMS report
 *
 * @param file - The Excel file to parse
 * @returns Promise - Resolves with parsed alliance data
 */
export function parseFmsAlliancesFile(file: File): Promise<FmsAlliancesResult> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e: ProgressEvent<FileReader>) => {
      try {
        const data = e.target?.result;
        if (!data) {
          reject(new Error("No data in file"));
          return;
        }

        const workbook = XLSX.read(data, { type: "binary" });
        const firstSheet = workbook.SheetNames[0];
        const sheet = workbook.Sheets[firstSheet];

        // Parse the Excel to array (headers start on 4th row, 0-indexed row 3)
        const rows = XLSX.utils.sheet_to_json(sheet, {
          range: 3,
          raw: false,
        }) as Record<string, string>[];

        if (!rows || rows.length === 0) {
          reject(new Error("No alliance data found in the file"));
          return;
        }

        // Get all column headers
        const headers = Object.keys(rows[0]);

        // Find the Teams column (case-insensitive)
        const teamsCol = headers.find((h) => h.toLowerCase().includes("teams"));

        if (!teamsCol) {
          reject(new Error("Could not find Teams column in the file"));
          return;
        }

        // Parse alliances
        const alliances: string[][] = [];
        for (const row of rows) {
          const teamsStr = row[teamsCol];
          if (!teamsStr || teamsStr.trim() === "") {
            // Skip empty rows
            continue;
          }

          // Split teams by comma and clean up
          const teams = teamsStr
            .split(",")
            .map((t) => t.trim())
            .filter((t) => t !== "")
            .map((t) => {
              // Remove any non-numeric characters and prepend 'frc'
              const teamNum = t.replace(/\D/g, "");
              return `frc${teamNum}`;
            });

          alliances.push(teams);
        }

        // Verify we have between 1 and 16 alliances
        if (alliances.length === 0 || alliances.length > 16) {
          reject(
            new Error(
              `Invalid number of alliances: ${alliances.length}. Expected 1-16.`
            )
          );
          return;
        }

        resolve({
          alliances,
          allianceCount: alliances.length,
        });
      } catch (error) {
        reject(new Error(`Error parsing file: ${(error as Error).message}`));
      }
    };

    reader.onerror = () => {
      reject(new Error("Error reading file"));
    };

    reader.readAsBinaryString(file);
  });
}
