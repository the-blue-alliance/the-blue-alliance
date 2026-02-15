# The Blue Alliance PWA (beta)

https://beta.thebluealliance.com/

## Development

If you don't have `pnpm`, you can install it with

```shellscript
npm i -g pnpm
```

or any of their strategies here: https://pnpm.io/installation

Install node deps:

```shellscript
pnpm i
```

Make sure you have your TBA APIv3 Read Key set in `.env`:

```sh
$ cp default.env .env
VITE_TBA_API_READ_KEY="myKey"
```

Run the dev server:

```shellscript
pnpm run dev
```

## Deployment

First, build your app for production:

```sh
pnpm run build
```

Then run the app in production mode:

```sh
pnpm start
```

## Data retrieval & caching

First, let's note the headers returned by the API for an example team info call:

```http
> curl -I https://www.thebluealliance.com/api/v3/team/frc254

200

accept-ranges: bytes
access-control-allow-origin: *
access-control-expose-headers: ETag
alt-svc: h3=":443"; ma=86400
cache-control: public, max-age=61, s-maxage=61
cf-cache-status: REVALIDATED
cf-ray: 9ac0dbf45d593c31-BOS
content-encoding: gzip
content-length: 475
content-type: application/json
date: Thu, 11 Dec 2025 00:27:57 GMT
etag: W/"b3cc50330998b038497f3f0ff99d466940392101"
nel: {"report_to":"cf-nel","success_fraction":0.0,"max_age":604800}
priority: u=0, i=?0
report-to: {"group":"cf-nel","max_age":604800,"endpoints":[{"url":"https://a.nel.cloudflare.com/report/v4?s=lG0gmvW9xsmg%2Bwi%2Fa8JyG4hJlhh8GuuI4mZ05abgKzncsZvo1iSyQmXo6gUj2I86kY%2BXNjl%2B6egDy5Fdhdq29DOB%2BrLE1n7knOsBb5c4q8GM1CQ9NV3R"}]}
server: cloudflare
server-timing: cfExtPri
vary: Accept-Encoding
x-cloud-trace-context: 67c0b4313f5451bf97b6defee9e1efc9
x-firefox-http3: h3
```

There are a few relevant cache headers here:

1. `cache-control` - this is the primary caching header; [MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)
2. `etag` - this is a hash that can be used on future client requests to ask the server if the content has changed; [MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/ETag)
3. `cf-cache-status` - this is used by Cloudflare to designate it's own cache state, which the TBA API lives behind; [CF Docs](https://developers.cloudflare.com/cache/concepts/cache-responses/)
4. `vary` - this is not relevant to us here but it is used for caching elsewhere in the world; [MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Vary)

When we receive an `etag` hash back from the server for our url, we can make a new request with a [`If-None-Match`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-None-Match) header to the TBA API in the future to ask if it's been modified:

```http
> curl -H 'If-None-Match: W/"b3cc50330998b038497f3f0ff99d466940392101"' \
     https://www.thebluealliance.com/api/v3/team/frc254

304

access-control-allow-origin: *
access-control-expose-headers: ETag
alt-svc: h3=":443"; ma=86400
cache-control: public, max-age=61, s-maxage=61
cf-cache-status: REVALIDATED
cf-ray: 9ac0ee0dcfbf4cf8-BOS
date: Thu, 11 Dec 2025 00:40:18 GMT
etag: W/"b3cc50330998b038497f3f0ff99d466940392101"
nel: {"report_to":"cf-nel","success_fraction":0.0,"max_age":604800}
report-to: {"group":"cf-nel","max_age":604800,"endpoints":[{"url":"https://a.nel.cloudflare.com/report/v4?s=2JqAwk7wPkWPYUysBIFa9AHo%2BqSmJ3z6eATyvVtsXvx2U8S43MNmpktryGv02VYc0g12jwBL8WGpqIhekDoU2nJ4uJaNZH5shDxlfd10EcDRthl57A%3D%3D"}]}
server: cloudflare
vary: Accept-Encoding
x-cloud-trace-context: 67c0b4313f5451bf97b6defee9e1efc9
x-firefox-spdy: h2
```

Note that the HTTP response code is now `304`, which means the server confirmed our cached version is still the latest version of the data. The response contains no body (JSON), which allows clients to skip downloading the same data over and over again.

With all that said... There are various levels of caching available when making an site like TBA Beta (heavy reads from a well cached public API).

1. `fetch()` calls
   - This is best done by utilizing a combination of `cache-control`, `etag`, or other headers (like [`Expires`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Expires), [`Last-Modified`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Last-Modified), or [`If-Modified-Since`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Modified-Since)).
   - All major browsers will automatically & intelligently obey all of the caching-related headers I mentioned above (except the Cloudflare one, which is proprietary).
   - Most Node.js `fetch()` implementations don't automatically do this (some do, like [Undici](https://github.com/nodejs/undici))
2. TanStack Query cache layer
   - This is a library that effectively wraps `fetch()` into a more state-management oriented philosophy
   - There are a [_lot_ of docs](https://tanstack.com/query/latest) on this
3. TanStack Router cache layer
   - Router caches `loader` data _per-route_ for us automatically
   - [Docs here](https://tanstack.com/router/v1/docs/framework/react/guide/data-loading)
   - Anything that is cached on the server is JSON-ified and sent to the client. So a larger server cache implies a slower first paint.
4. Cache the entire html response
   - This is what the prod site does
   - But TanStack Router / React don't support this extremely well out of the box

## Styling

TBA Beta uses [TailwindCSS](https://tailwindcss.com/) and [ShadCN](https://ui.shadcn.com/) components.

## Icons

Icons are complicated and opinionated. TBA uses `@unplugin/unplugin-icons`, which combines two nice tools:

- `unplugin`, which allows you to write build plugins for any frontend build system
- `Iconify`, which allows you to use any of the many, many icon packs out there in a shared syntax/format

Unfortunately, Iconify wants you to get the icons from their API, but we'd rather have the SVGs in the project locally. Unplugin makes this easy:

1. Go to the [Iconify sets](https://icon-sets.iconify.design/)
2. Find an icon; either search a specific set or search a keyword across all sets.
3. Click the icon to bring up a dialog box.
4. Click the `Unplugin Icons` tab.
5. Copy the generated `import ...` string.
6. Use your imported component as a regular React component (e.g. `<MdiMyIcon />`).

## Adding environment variables

1. Put some form of example in `default.env`
2. Add the environment variable to `app/vite-env.d.ts`
3. Add a validator to `vite.config.ts`
4. You can then reference it in code with `import.env.meta.VITE_MY_VAR`.

## PR Screenshots

PRs that touch `pwa/` files automatically get before/after screenshots posted as a PR comment (via the `PWA Screenshots` workflow). By default, the Homepage, a Team page, and an Event page are captured.

To request screenshots of additional pages, add a `## Screenshot Pages` section to your PR description:

```markdown
## Screenshot Pages
- /match/2024mil_f1m2
- /team/254/2024 Team 254 Page
- /gameday
```

Each line is `- /path` optionally followed by a display name. The workflow parses this section and adds those pages to the screenshot set.

> **Note:** Screenshots require the `TBA_API_READ_KEY` secret, which is only available for same-repo branches (not fork PRs). Fork PRs will gracefully skip screenshot capture.

## Playwright tests

Playwright (end to end) tests are within `./tests`. Test names with `mobile` in the name will be run on mobile; others will be run on desktop viewports.

```sh
# Runs the end-to-end tests.
pnpm dlx playwright test

# Starts the interactive UI mode.
pnpm dlx playwright test --ui

# Runs the tests only on Desktop Chrome.
pnpm dlx playwright test --project=chromium

# Runs the tests in a specific file.
pnpm dlx playwright test example

# Runs the tests in debug mode.
pnpm dlx playwright test --debug

# Auto generate tests with Codegen.
pnpm dlx playwright codegen

# Auto generate tests with a specific device
pnpm dlx playwright codegen --device="Pixel 7"
```
