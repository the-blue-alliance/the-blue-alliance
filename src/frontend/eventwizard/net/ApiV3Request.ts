import ensureRequestSuccess from "./EnsureRequestSuccess";

async function makeApiV3Request(authId: string, requestPath: string): Promise<Response> {
  const headers = new Headers();
  headers.append("X-TBA-Auth-Key", authId);

  const response = await fetch(requestPath, {
    method: "GET",
    headers: headers,
    credentials: "same-origin",
  });
  
  return ensureRequestSuccess(response);
}

export default makeApiV3Request;
