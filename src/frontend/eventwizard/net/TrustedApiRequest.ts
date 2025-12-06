// @ts-ignore - md5 types not available
import md5 from "md5";
import ensureRequestSuccess from "./EnsureRequestSuccess";

async function makeTrustedApiRequest(
  authId: string,
  authSecret: string,
  requestPath: string,
  requestBody: string
): Promise<Response> {
  const authSig = md5(authSecret + requestPath + requestBody);
  const headers = new Headers();
  headers.append("X-TBA-Auth-Id", authId);
  headers.append("X-TBA-Auth-Sig", authSig);
  
  const response = await fetch(requestPath, {
    method: "POST",
    headers: headers,
    credentials: "same-origin",
    body: requestBody,
  });
  
  return ensureRequestSuccess(response);
}

export default makeTrustedApiRequest;
