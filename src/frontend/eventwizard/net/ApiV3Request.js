/**
 * Makes an authenticated GET request to TBA API v3
 * @param {string} authId - The X-TBA-Auth-Key to use for authentication
 * @param {string} requestPath - The API path (e.g., '/api/v3/event/2024nytr/matches/simple')
 * @param {function} onSuccess - Callback function called with response data on success
 * @param {function} onError - Callback function called with error message on failure
 */
const makeApiV3Request = (authId, requestPath, onSuccess, onError) => {
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
    .then((data) => {
      onSuccess(data);
    })
    .catch((error) => {
      onError(error.message);
    });
};

export default makeApiV3Request;
