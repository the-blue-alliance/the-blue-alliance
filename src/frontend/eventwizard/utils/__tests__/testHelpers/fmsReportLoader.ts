import fs from "fs";
import path from "path";

/**
 * Load a test file from a relative path and create a File object.
 * @param relativePathSegments - Path segments relative to the test file location
 * @param filename - Name of the file
 * @returns File object containing the file data
 */
export function loadTestFile(
  relativePathSegments: string[],
  filename: string
): File {
  const filePath = path.join(...relativePathSegments, filename);
  const buffer = fs.readFileSync(filePath);
  return new File([buffer], filename, {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
}
