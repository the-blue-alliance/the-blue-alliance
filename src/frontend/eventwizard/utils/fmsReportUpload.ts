/**
 * Uploads an FMS report file to the backend for archival
 * 
 * @param file - The FMS report file to upload
 * @param eventKey - The event key (e.g., "2024cmp")
 * @param reportType - The type of report (e.g., "qual_rankings", "qual_schedule", "qual_results", "playoff_alliances", "team_list")
 * @returns Promise that resolves when the upload is complete
 */
export async function uploadFmsReport(
  file: File,
  eventKey: string,
  reportType: string,
  makeTrustedRequest: (requestPath: string, requestBody: string | FormData) => Promise<Response>
): Promise<void> {
  // Calculate SHA-256 digest of the file
  const fileBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest("SHA-256", fileBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const fileDigest = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");

  const formData = new FormData();
  formData.append("reportFile", file);
  formData.append("fileDigest", fileDigest);
  
  await makeTrustedRequest(
    `/api/trusted/v1/event/${eventKey}/fms_reports/${reportType}`,
    formData
  );
}
