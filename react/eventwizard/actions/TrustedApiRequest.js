import md5 from 'md5'

function makeTrustedApiRequest(auth_id, auth_secret, request_path, request_body, on_success, on_error) {
  const auth_sig = md5(auth_secret + request_path + request_body);
  const headers = new Headers();
  headers.append('X-TBA-Auth-Id', auth_id);
  headers.append('X-TBA-Auth-Sig', auth_sig);
  return fetch(request_path, {
    method: "POST",
    credentials: 'same-origin',
    body: request_body,
  })
    .then(function(response) {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response;
    })
    .then(on_success)
    .catch(on_error);
}

export default makeTrustedApiRequest