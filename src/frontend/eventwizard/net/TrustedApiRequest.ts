// @ts-ignore - md5 types not available
import md5 from "md5";
import ensureRequestSuccess from "./EnsureRequestSuccess";

async function makeTrustedApiRequest(
  authId: string,
  authSecret: string,
  requestPath: string,
  requestBody: string | FormData
): Promise<Response> {
  const headers = new Headers();
  headers.append("X-TBA-Auth-Id", authId);

  if (!(requestBody instanceof FormData)) {
    const authSig = md5(authSecret + requestPath + requestBody);
    headers.append("X-TBA-Auth-Sig", authSig);
  } else if ((requestBody as FormData).has("fileDigest")) {
    const fileDigest = (requestBody as FormData).get("fileDigest") as string;
    const authSig = md5(authSecret + requestPath + fileDigest);
    headers.append("X-TBA-Auth-Sig", authSig);
  }
  
  const response = await fetch(requestPath, {
    method: "POST",
    headers: headers,
    credentials: "same-origin",
    body: requestBody,
  });
  
  return ensureRequestSuccess(response);
}

export default makeTrustedApiRequest;
