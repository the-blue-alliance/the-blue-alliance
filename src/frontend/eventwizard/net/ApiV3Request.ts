/**
 * Makes an authenticated GET request to TBA API v3
 * @param authId - The X-TBA-Auth-Key to use for authentication
 * @param requestPath - The API path (e.g., '/api/v3/event/2024nytr/matches/simple')
 * @param onSuccess - Callback function called with response data on success
 * @param onError - Callback function called with error message on failure
 */
const makeApiV3Request = <T = unknown>(
  authId: string,
  requestPath: string,
  onSuccess: (data: T) => void,
  onError: (error: string) => void
): void => {
  const headers = new Headers();
  headers.append("X-TBA-Auth-Key", authId);

  fetch(requestPath, {
    method: "GET",
    headers: headers,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data: T) => {
      onSuccess(data);
    })
    .catch((error: Error) => {
      onError(error.message);
    });
};

export default makeApiV3Request;
