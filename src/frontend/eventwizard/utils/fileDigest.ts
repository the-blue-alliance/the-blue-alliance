/**
 * Calculates the SHA-256 digest of a file
 *
 * @param file - The file to calculate the digest for
 * @returns Promise that resolves to the hex-encoded SHA-256 digest
 */
export async function calculateFileDigest(file: File): Promise<string> {
  const fileBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest("SHA-256", fileBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}
