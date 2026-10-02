export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Map a client failure to an ApiError only when there is a genuine non-2xx HTTP
// response (status drives retry + 404-skip logic in queryClient). A 2xx whose
// body failed to parse/validate throws inside the client's try block with
// response.ok === true — preserve that real error instead of mislabeling it as
// "ApiError: 200". Network failures (no response) also pass through unchanged.
export function mapClientError(error: unknown, response?: Response): unknown {
  if (response && !response.ok) {
    return new ApiError(
      response.statusText || String(response.status),
      response.status,
    );
  }
  return error;
}
