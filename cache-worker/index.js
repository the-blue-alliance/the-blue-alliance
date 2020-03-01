addEventListener('fetch', event => {
  event.passThroughOnException()
  event.respondWith(handleRequest(event))
})

async function handleRequest(event) {
  let response = await caches.default.match(event.request)
  if (response) {
    const age = parseInt(response.headers.get('age'))
    const cacheControl = response.headers.get('cache-control')

    if (cacheControl) {
      const matches = cacheControl.match(/max-age=(\d+)/)
      const maxAge = matches ? parseInt(matches[1]) : null

      // Ensure our Edge Cache TTL is as-expected (age <= max-age)
      // If our age > maxAge, something has gone wrong
      if (age && maxAge && age > maxAge) {
        // Bypass our Cloudflare cache - get a fresh response
        await caches.default.delete(event.request)
        response = await fetch(event.request)
        // Add some debugging information to our response for monitoring
        response = new Response(response.body, response)
        response.headers.set('X-TBA-Cache-Status', 'invalidated')
      }
    }
  } else {
    // Page is not cached - fetch/store from origin accordingly
    response = await fetch(event.request)
  }
  return response
}
