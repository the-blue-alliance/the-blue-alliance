/**
 * Uploads an FMS report file to the backend for archival
 * 
 * @param file - The FMS report file to upload
 * @param eventKey - The event key (e.g., "2024cmp")
 * @param reportType - The type of report (e.g., "qual_rankings", "qual_schedule", "qual_results", "playoff_alliances", "team_list")
 * @returns Promise that resolves when the upload is complete
 */
import { calculateFileDigest } from "./fileDigest";

export async function uploadFmsReport(
  file: File,
  eventKey: string,
  reportType: string,
  makeTrustedRequest: (requestPath: string, requestBody: string | FormData) => Promise<Response>
): Promise<void> {
  const fileDigest = await calculateFileDigest(file);

  const formData = new FormData();
  formData.append("reportFile", file);
  formData.append("fileDigest", fileDigest);
  
  await makeTrustedRequest(
    `/api/_eventwizard/event/${eventKey}/fms_reports/${reportType}`,
    formData
  );
}
