import md5 from 'md5'
import ensureRequestSuccess from './EnsureRequestSuccess'

function makeTrustedApiRequest(authId, authSecret, requestPath, requestBody, onSuccess, onError) {
  const authSig = md5(authSecret + requestPath + requestBody)
  const headers = new Headers()
  headers.append('X-TBA-Auth-Id', authId)
  headers.append('X-TBA-Auth-Sig', authSig)
  return fetch(requestPath, {
    method: 'POST',
    credentials: 'same-origin',
    body: requestBody,
  })
    .then(ensureRequestSuccess)
    .then(onSuccess)
    .catch(onError)
}

export default makeTrustedApiRequest
