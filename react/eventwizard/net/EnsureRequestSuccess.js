function ensureRequestSuccess(response) {
  if (!response.ok) {
    throw new Error(response.statusText)
  }
  return response
}

export default ensureRequestSuccess
