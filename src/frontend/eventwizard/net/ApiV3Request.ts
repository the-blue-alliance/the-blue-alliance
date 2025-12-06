/**
 * Makes an authenticated GET request to TBA API v3
 * @param authId - The X-TBA-Auth-Key to use for authentication
 * @param requestPath - The API path (e.g., '/api/v3/event/2024nytr/matches/simple')
 * @returns Promise that resolves to the parsed JSON response data
 */
const makeApiV3Request = async <T = unknown>(
  authId: string,
  requestPath: string
): Promise<T> => {
  const headers = new Headers();
  headers.append("X-TBA-Auth-Key", authId);

  const response = await fetch(requestPath, {
    method: "GET",
    headers: headers,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

export default makeApiV3Request;
