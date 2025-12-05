// @ts-ignore - md5 types not available
import md5 from "md5";
import ensureRequestSuccess from "./EnsureRequestSuccess";

function makeTrustedApiRequest(
  authId: string,
  authSecret: string,
  requestPath: string,
  requestBody: string,
  onSuccess: (response: Response) => void,
  onError: (error: Error) => void
): Promise<void> {
  const authSig = md5(authSecret + requestPath + requestBody);
  const headers = new Headers();
  headers.append("X-TBA-Auth-Id", authId);
  headers.append("X-TBA-Auth-Sig", authSig);
  return fetch(requestPath, {
    method: "POST",
    headers: headers,
    credentials: "same-origin",
    body: requestBody,
  })
    .then(ensureRequestSuccess)
    .then(onSuccess)
    .catch(onError);
}

export default makeTrustedApiRequest;
