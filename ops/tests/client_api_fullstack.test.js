const fetch = require("node-fetch");

async function postToAuthEmulator(endpoint, body) {
  const url =
    "http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:" +
    endpoint +
    "?key=testing_key";
  return await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

async function postToClientAPI(endpoint, idToken, body) {
  return await fetch(
    "http://localhost:8080/clientapi/tbaClient/v9/" + endpoint,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + idToken,
      },
      body: JSON.stringify(body),
    }
  );
}

async function getIdToken() {
  // When running against a local instance, the user might already exist
  // So we can handle that case
  const body = {
    email: "integration_test@thebluealliance.com",
    password: "this_is_only_a_test",
  };
  const registerResp = await postToAuthEmulator("signUp", body);

  const registerRespBody = await registerResp.json();
  if (
    registerResp.status == 400 &&
    registerRespBody.error.errors[0].message == "EMAIL_EXISTS"
  ) {
    const tokenResp = await postToAuthEmulator("signInWithPassword", body);
    expect(tokenResp.status).toEqual(200);
    return (await tokenResp.json()).idToken;
  } else {
    return registerRespBody.idToken;
  }
}

describe("Mobile device registration", () => {
  let idToken = null;
  it("can fetch an auth token", async () => {
    idToken = await getIdToken();
  });

  const device = {
    name: "Test Device",
    operating_system: "test",
    mobile_id: "abc123",
    device_uuid: "test",
  };

  it("should register successfully", async () => {
    const regRes = await postToClientAPI("register", idToken, device);
    expect(regRes.status).toEqual(200);
    expect(await regRes.json()).toEqual({
      code: 200,
      message: "Registration successful",
    });
  });

  it("should return the newly registered device", async () => {
    const listRes = await postToClientAPI("list_clients", idToken, {});
    expect(listRes.status).toEqual(200);
    expect(await listRes.json()).toEqual({
      code: 200,
      message: "",
      devices: [device],
    });
  });

  it("should unregister successfully", async () => {
    const unregReq = await postToClientAPI("unregister", idToken, device);
    expect(unregReq.status).toEqual(200);
    expect(await unregReq.json()).toEqual({
      code: 200,
      message: "User deleted",
    });
  });

  it("should should no longer return the device", async () => {
    const listRes = await postToClientAPI("list_clients", idToken, {});
    expect(listRes.status).toEqual(200);
    expect(await listRes.json()).toEqual({
      code: 200,
      message: "",
      devices: [],
    });
  });
});
