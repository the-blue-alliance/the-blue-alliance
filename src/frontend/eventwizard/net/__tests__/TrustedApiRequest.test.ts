import makeTrustedApiRequest from "../TrustedApiRequest";
import md5 from "md5";

describe("makeTrustedApiRequest", () => {
  let mockFetch: jest.Mock;

  beforeEach(() => {
    mockFetch = jest.fn();
    global.fetch = mockFetch as any;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("makes a POST request with X-TBA-Auth-Id and X-TBA-Auth-Sig headers for string body", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const authSecret = "test-secret";
    const requestPath = "/api/trusted/v1/event/2024cmp/rankings/update";
    const requestBody = '{"rankings": []}';

    await makeTrustedApiRequest(authId, authSecret, requestPath, requestBody);

    expect(mockFetch).toHaveBeenCalledWith(requestPath, {
      method: "POST",
      headers: expect.any(Headers),
      credentials: "same-origin",
      body: requestBody,
    });
  });

  it("includes X-TBA-Auth-Id in headers for string body", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id-123";
    const authSecret = "test-secret";
    const requestPath = "/api/trusted/v1/event/2024cmp/rankings/update";
    const requestBody = '{"rankings": []}';

    await makeTrustedApiRequest(authId, authSecret, requestPath, requestBody);

    const callArgs = mockFetch.mock.calls[0];
    const headers = callArgs[1].headers;
    expect(headers.get("X-TBA-Auth-Id")).toBe(authId);
  });

  it("computes correct MD5 signature for string body", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const authSecret = "test-secret";
    const requestPath = "/api/trusted/v1/event/2024cmp/rankings/update";
    const requestBody = '{"rankings": []}';
    const expectedSig = md5(authSecret + requestPath + requestBody);

    await makeTrustedApiRequest(authId, authSecret, requestPath, requestBody);

    const callArgs = mockFetch.mock.calls[0];
    const headers = callArgs[1].headers;
    expect(headers.get("X-TBA-Auth-Sig")).toBe(expectedSig);
  });

  it("makes a POST request with FormData for file upload", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const authSecret = "test-secret";
    const requestPath = "/api/trusted/v1/event/2024cmp/fms_reports/qual_rankings";
    
    const formData = new FormData();
    const mockFile = new File(["test file content"], "rankings.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    formData.append("reportFile", mockFile);
    formData.append("fileDigest", "abcd1234");

    await makeTrustedApiRequest(authId, authSecret, requestPath, formData);

    expect(mockFetch).toHaveBeenCalledWith(requestPath, {
      method: "POST",
      headers: expect.any(Headers),
      credentials: "same-origin",
      body: formData,
    });
  });

  it("includes X-TBA-Auth-Id in headers for FormData with fileDigest", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const authSecret = "test-secret";
    const requestPath = "/api/trusted/v1/event/2024cmp/fms_reports/qual_rankings";
    
    const formData = new FormData();
    const mockFile = new File(["test file content"], "rankings.xlsx");
    formData.append("reportFile", mockFile);
    formData.append("fileDigest", "abcd1234");

    await makeTrustedApiRequest(authId, authSecret, requestPath, formData);

    const callArgs = mockFetch.mock.calls[0];
    const headers = callArgs[1].headers;
    expect(headers.get("X-TBA-Auth-Id")).toBe(authId);
  });

  it("computes correct MD5 signature using fileDigest for FormData", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const authSecret = "test-secret";
    const requestPath = "/api/trusted/v1/event/2024cmp/fms_reports/qual_rankings";
    const fileDigest = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"; // SHA-256 of empty string

    const formData = new FormData();
    const mockFile = new File([""], "test.xlsx");
    formData.append("reportFile", mockFile);
    formData.append("fileDigest", fileDigest);

    const expectedSig = md5(authSecret + requestPath + fileDigest);

    await makeTrustedApiRequest(authId, authSecret, requestPath, formData);

    const callArgs = mockFetch.mock.calls[0];
    const headers = callArgs[1].headers;
    expect(headers.get("X-TBA-Auth-Sig")).toBe(expectedSig);
  });

  it("does not include X-TBA-Auth-Sig for FormData without fileDigest", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const authSecret = "test-secret";
    const requestPath = "/api/trusted/v1/event/2024cmp/fms_reports/qual_rankings";
    
    const formData = new FormData();
    const mockFile = new File(["test content"], "test.xlsx");
    formData.append("reportFile", mockFile);

    await makeTrustedApiRequest(authId, authSecret, requestPath, formData);

    const callArgs = mockFetch.mock.calls[0];
    const headers = callArgs[1].headers;
    expect(headers.get("X-TBA-Auth-Sig")).toBeNull();
  });

  it("throws error on failed response", async () => {
    const mockResponse = {
      ok: false,
      status: 401,
      text: jest.fn().mockResolvedValue("Unauthorized"),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const authSecret = "test-secret";
    const requestPath = "/api/trusted/v1/event/2024cmp/rankings/update";
    const requestBody = '{"rankings": []}';

    await expect(
      makeTrustedApiRequest(authId, authSecret, requestPath, requestBody)
    ).rejects.toThrow();
  });
});
