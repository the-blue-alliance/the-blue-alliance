import makeApiV3Request from "../ApiV3Request";

describe("makeApiV3Request", () => {
  let mockFetch: jest.Mock;

  beforeEach(() => {
    mockFetch = jest.fn();
    global.fetch = mockFetch as any;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("makes a GET request with X-TBA-Auth-Key header", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ data: "test" }),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024nytr/matches/simple";

    await makeApiV3Request(authId, requestPath);

    expect(mockFetch).toHaveBeenCalledWith(requestPath, {
      method: "GET",
      headers: expect.any(Headers),
    });
  });

  it("includes X-TBA-Auth-Key in headers", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ data: "test" }),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id-123";
    const requestPath = "/api/v3/event/2024nytr/matches/simple";

    await makeApiV3Request(authId, requestPath);

    const callArgs = mockFetch.mock.calls[0];
    const headers = callArgs[1].headers;
    expect(headers.get("X-TBA-Auth-Key")).toBe(authId);
  });

  it("returns parsed JSON data on successful response", async () => {
    const mockData = [
      { key: "2024nytr_qm1", match_number: 1 },
      { key: "2024nytr_qm2", match_number: 2 },
    ];
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue(mockData),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024nytr/matches/simple";

    const result = await makeApiV3Request(authId, requestPath);

    expect(result).toEqual(mockData);
  });

  it("throws error when response is not ok", async () => {
    const mockResponse = {
      ok: false,
      status: 404,
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024invalid/matches/simple";

    await expect(makeApiV3Request(authId, requestPath)).rejects.toThrow(
      "HTTP error! status: 404"
    );
  });

  it("throws error when fetch throws", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024nytr/matches/simple";

    await expect(makeApiV3Request(authId, requestPath)).rejects.toThrow(
      "Network error"
    );
  });

  it("throws error when JSON parsing fails", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockRejectedValue(new Error("Invalid JSON")),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024nytr/matches/simple";

    await expect(makeApiV3Request(authId, requestPath)).rejects.toThrow(
      "Invalid JSON"
    );
  });

  it("uses GET method for all requests", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024nytr/teams/simple";

    await makeApiV3Request(authId, requestPath);

    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[1].method).toBe("GET");
  });
});
