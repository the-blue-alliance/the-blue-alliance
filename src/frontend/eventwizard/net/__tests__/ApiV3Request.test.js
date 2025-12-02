import makeApiV3Request from "../ApiV3Request";

describe("makeApiV3Request", () => {
  let mockFetch;

  beforeEach(() => {
    mockFetch = jest.fn();
    global.fetch = mockFetch;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("makes a GET request with X-TBA-Auth-Key header", () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ data: "test" }),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024nytr/matches/simple";
    const onSuccess = jest.fn();
    const onError = jest.fn();

    makeApiV3Request(authId, requestPath, onSuccess, onError);

    expect(mockFetch).toHaveBeenCalledWith(requestPath, {
      method: "GET",
      headers: expect.any(Headers),
    });
  });

  it("includes X-TBA-Auth-Key in headers", () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ data: "test" }),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id-123";
    const requestPath = "/api/v3/event/2024nytr/matches/simple";
    const onSuccess = jest.fn();
    const onError = jest.fn();

    makeApiV3Request(authId, requestPath, onSuccess, onError);

    const callArgs = mockFetch.mock.calls[0];
    const headers = callArgs[1].headers;
    expect(headers.get("X-TBA-Auth-Key")).toBe(authId);
  });

  it("calls onSuccess with parsed JSON data on successful response", async () => {
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
    const onSuccess = jest.fn();
    const onError = jest.fn();

    await makeApiV3Request(authId, requestPath, onSuccess, onError);

    // Wait for promises to resolve
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(onSuccess).toHaveBeenCalledWith(mockData);
    expect(onError).not.toHaveBeenCalled();
  });

  it("calls onError with error message when response is not ok", async () => {
    const mockResponse = {
      ok: false,
      status: 404,
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024invalid/matches/simple";
    const onSuccess = jest.fn();
    const onError = jest.fn();

    await makeApiV3Request(authId, requestPath, onSuccess, onError);

    // Wait for promises to resolve
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(onSuccess).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith("HTTP error! status: 404");
  });

  it("calls onError with error message when fetch throws", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024nytr/matches/simple";
    const onSuccess = jest.fn();
    const onError = jest.fn();

    await makeApiV3Request(authId, requestPath, onSuccess, onError);

    // Wait for promises to resolve
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(onSuccess).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith("Network error");
  });

  it("calls onError when JSON parsing fails", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockRejectedValue(new Error("Invalid JSON")),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024nytr/matches/simple";
    const onSuccess = jest.fn();
    const onError = jest.fn();

    await makeApiV3Request(authId, requestPath, onSuccess, onError);

    // Wait for promises to resolve
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(onSuccess).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith("Invalid JSON");
  });

  it("uses GET method for all requests", () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const authId = "test-auth-id";
    const requestPath = "/api/v3/event/2024nytr/teams/simple";
    const onSuccess = jest.fn();
    const onError = jest.fn();

    makeApiV3Request(authId, requestPath, onSuccess, onError);

    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[1].method).toBe("GET");
  });
});
