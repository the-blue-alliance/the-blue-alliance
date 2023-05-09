const fetch = require("node-fetch");
const http = require("http");

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
    expect([200, 304]).toContainEqual(listRes.status);

    const respBody = await listRes.json();
    expect(respBody.code).toEqual(200);
    expect(respBody.devices).toContainEqual(device);
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

    const respBody = await listRes.json();
    expect(respBody.code).toEqual(200);
    expect(respBody.devices).not.toContainEqual(device);
  });
});

describe("webhook ping", () => {
  let idToken = null;
  it("can fetch an auth token", async () => {
    idToken = await getIdToken();
  });

  const device = {
    name: "Test Device",
    operating_system: "webhook",
    mobile_id: "http://localhost:8080/local/webhooks",
    device_uuid: "test",
  };
  it("should register successfully", async () => {
    const regRes = await postToClientAPI("register", idToken, device);
    expect(regRes.status).toEqual(200);

    const respBody = await regRes.json();
    expect([200, 304]).toContainEqual(respBody.code);
  });
  it("can ping the device", async () => {
    const pingRes = await postToClientAPI("ping", idToken, device);
    expect(pingRes.status).toEqual(200);
    expect(await pingRes.json()).toEqual({
      code: 200,
      message: "Ping sent",
    });
  });
  it("can receive webhook message", async () => {
    const fetchResp = await fetch("http://localhost:8080/local/webhooks", {
      method: "GET",
    });
    expect(fetchResp.status).toEqual(200);

    const respBody = await fetchResp.json();
    expect(respBody).toEqual({
      message_type: "ping",
      message_data: {
        title: "Test Notification",
        desc: "This is a test message ensuring your device can recieve push messages from The Blue Alliance.",
      },
    });
  });
});
