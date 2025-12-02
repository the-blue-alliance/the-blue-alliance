import XLSX from "xlsx";

/**
 * Parse FMS Rankings Excel file
 * This parser is year-agnostic and doesn't depend on specific column headers
 *
 * @param {File} file - The Excel file to parse
 * @returns {Promise} - Resolves with parsed rankings data
 */
export function parseRankingsFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = e.target.result;
        const workbook = XLSX.read(data, { type: "binary" });
        const firstSheet = workbook.SheetNames[0];
        const sheet = workbook.Sheets[firstSheet];

        // Parse the Excel to array of rankings (headers start on 5th row)
        const rankings = XLSX.utils.sheet_to_json(sheet, {
          range: 4,
          raw: false,
        });

        if (!rankings || rankings.length === 0) {
          reject(new Error("No rankings found in the file"));
          return;
        }

        // Get all column headers from the first row
        const allHeaders = Object.keys(rankings[0]);

        // Identify standard columns
        const rankCol = allHeaders.find((h) =>
          h.toLowerCase().includes("rank")
        );
        const teamCol = allHeaders.find((h) =>
          h.toLowerCase().includes("team")
        );
        const recordCol = allHeaders.find(
          (h) =>
            h.toLowerCase().includes("w-l-t") || h.toLowerCase().includes("wlt")
        );
        const dqCol = allHeaders.find((h) => h.toLowerCase().includes("dq"));
        const playedCol = allHeaders.find((h) =>
          h.toLowerCase().includes("played")
        );

        if (!rankCol || !teamCol) {
          reject(
            new Error(
              'Could not find required columns "Rank" and "Team" in the rankings file'
            )
          );
          return;
        }

        // Breakdown columns are all columns except the standard ones
        const standardCols = [rankCol, teamCol, recordCol, dqCol, playedCol];
        const breakdownCols = allHeaders.filter(
          (h) => !standardCols.includes(h)
        );

        const parsedRankings = [];

        for (let i = 0; i < rankings.length; i++) {
          const row = rankings[i];

          // Check for invalid row
          if (!row[rankCol] || isNaN(parseInt(row[rankCol]))) {
            continue;
          }

          const teamNum = parseInt(row[teamCol]);
          if (!teamNum || isNaN(teamNum) || teamNum <= 0) {
            continue;
          }

          // Parse W-L-T record
          let wins = 0;
          let losses = 0;
          let ties = 0;
          if (recordCol && row[recordCol]) {
            const recordParts = row[recordCol].toString().split("-");
            if (recordParts.length === 3) {
              wins = parseInt(recordParts[0]) || 0;
              losses = parseInt(recordParts[1]) || 0;
              ties = parseInt(recordParts[2]) || 0;
            }
          }

          const ranking = {
            team_key: `frc${teamNum}`,
            rank: parseInt(row[rankCol]),
            wins,
            losses,
            ties,
            played: playedCol ? parseInt(row[playedCol]) || 0 : 0,
            dqs: dqCol ? parseInt(row[dqCol]) || 0 : 0,
          };

          // Add breakdown values
          for (const col of breakdownCols) {
            const value = row[col];
            // Try to parse as number if possible, otherwise keep as string
            if (value !== null && value !== undefined && value !== "") {
              const numValue = parseFloat(value.toString().replace(",", ""));
              ranking[col] = isNaN(numValue) ? value : numValue;
            }
          }

          parsedRankings.push(ranking);
        }

        resolve({
          breakdowns: breakdownCols,
          rankings: parsedRankings,
          headers: allHeaders,
        });
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => {
      reject(new Error("Failed to read file"));
    };

    reader.readAsBinaryString(file);
  });
}
