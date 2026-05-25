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
$ cp .env.example .env
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

## Color

It's important to be familiar with some color resources before adding or modifying colors:

- https://stripe.com/blog/accessible-color-systems
- https://evilmartians.com/chronicles/oklch-in-css-why-quit-rgb-hsl
- https://oklch.fyi/
- https://lea.verou.me/blog/tags/color/
- https://git.apcacontrast.com/documentation/WhyAPCA.html

The following colors (defined in `app/style/colors/`) were rigorously analyzed and chosen deliberately:

|                                                   | Name    | OKLCH                        | Hex       |
| ------------------------------------------------- | ------- | ---------------------------- | --------- |
| ![](https://placehold.co/16x16/3f51b5/3f51b5.png) | Primary | `oklch(0.4782 0.1589 271.4)` | `#3f51b5` |

**Alliance — light mode**

|                                                   | Name        | OKLCH                          | Hex       |
| ------------------------------------------------- | ----------- | ------------------------------ | --------- |
| ![](https://placehold.co/16x16/fbb4a8/fbb4a8.png) | Red winner  | `oklch(0.832852 0.085938 29)`  | `#fbb4a8` |
| ![](https://placehold.co/16x16/fed7d1/fed7d1.png) | Red loser   | `oklch(0.910855 0.04375 29)`   | `#fed7d1` |
| ![](https://placehold.co/16x16/a9c6fe/a9c6fe.png) | Blue winner | `oklch(0.824681 0.085938 264)` | `#a9c6fe` |
| ![](https://placehold.co/16x16/d2e1fe/d2e1fe.png) | Blue loser  | `oklch(0.906397 0.04375 264)`  | `#d2e1fe` |

**Alliance — dark mode**

|                                                   | Name        | OKLCH                       | Hex       |
| ------------------------------------------------- | ----------- | --------------------------- | --------- |
| ![](https://placehold.co/16x16/a23127/a23127.png) | Red winner  | `oklch(0.482064 0.15 29)`   | `#a23127` |
| ![](https://placehold.co/16x16/4e1c17/4e1c17.png) | Red loser   | `oklch(0.30319 0.077 29)`   | `#4e1c17` |
| ![](https://placehold.co/16x16/3056b0/3056b0.png) | Blue winner | `oklch(0.477592 0.15 264)`  | `#3056b0` |
| ![](https://placehold.co/16x16/1a2c55/1a2c55.png) | Blue loser  | `oklch(0.302296 0.077 264)` | `#1a2c55` |

**Alliance accents — light mode** (used as a background; no text is placed on top)

|                                                   | Name | OKLCH                          | Hex       |
| ------------------------------------------------- | ---- | ------------------------------ | --------- |
| ![](https://placehold.co/16x16/ff9789/ff9789.png) | Red  | `oklch(0.781918 0.126563 29)`  | `#ff9789` |
| ![](https://placehold.co/16x16/8fb4fe/8fb4fe.png) | Blue | `oklch(0.770976 0.114063 264)` | `#8fb4fe` |

**Alliance accents — dark mode** (used as a background; no text is placed on top)

|                                                   | Name | OKLCH                          | Hex       |
| ------------------------------------------------- | ---- | ------------------------------ | --------- |
| ![](https://placehold.co/16x16/ff4537/ff4537.png) | Red  | `oklch(0.663086 0.223438 29)`  | `#ff4537` |
| ![](https://placehold.co/16x16/5488fe/5488fe.png) | Blue | `oklch(0.650391 0.184375 264)` | `#5488fe` |

The other colors used across the site are just Tailwind or ShadCN colors that seemed to look good — they weren't rigorously analyzed like the above.

These colors were generated from [here](https://harmonizer.evilmartians.com/), with APCA contrasts of 70 and 85 on text colors `#1f1f1f` (for light mode) and `#e3e3e3` (for dark mode). These are all sRGB colors so they should be mostly consistent across device screens (OKLCH can attempt to display P3 colors which are not supported on every display). All reds have hue of 29 and all blues have a hue of 264 (except the primary brand color, which is separate).

The accent colors generally should not have text overtop of them. They can be used for borders, etc. They are rated to be used as text elements on both light and dark backgrounds as well.

The other colors that are being used across the site (that are not listed above) are just Tailwind or Shadcn colors that seemed to look good -- they weren't rigorously analyzed like the above.

**Districts**

These are mostly arbitrary values for each district. If your district has branding guidelines, please let us know.

|                                                   | Name              | Districts    | OKLCH                      | Hex       |
| ------------------------------------------------- | ----------------- | ------------ | -------------------------- | --------- |
| ![](https://placehold.co/16x16/FAB604/FAB604.png) | California        | `ca`         | `oklch(0.818 0.168 81.3)`  | `#FAB604` |
| ![](https://placehold.co/16x16/2FA4A9/2FA4A9.png) | Chesapeake        | `chs`, `fch` | `oklch(0.658 0.100 199.3)` | `#2FA4A9` |
| ![](https://placehold.co/16x16/E04B4B/E04B4B.png) | Indiana           | `fin`, `in`  | `oklch(0.620 0.186 24.3)`  | `#E04B4B` |
| ![](https://placehold.co/16x16/7DD3FC/7DD3FC.png) | Israel            | `isr`        | `oklch(0.828 0.101 230.3)` | `#7DD3FC` |
| ![](https://placehold.co/16x16/94A3B8/94A3B8.png) | Michigan          | `fim`        | `oklch(0.711 0.035 256.8)` | `#94A3B8` |
| ![](https://placehold.co/16x16/9A8FD1/9A8FD1.png) | Mid-Atlantic      | `fma`, `mar` | `oklch(0.685 0.096 291.3)` | `#9A8FD1` |
| ![](https://placehold.co/16x16/271380/271380.png) | New England       | `ne`         | `oklch(0.309 0.166 278.9)` | `#271380` |
| ![](https://placehold.co/16x16/7BA7D9/7BA7D9.png) | North Carolina    | `fnc`        | `oklch(0.716 0.088 252.2)` | `#7BA7D9` |
| ![](https://placehold.co/16x16/4F6EF7/4F6EF7.png) | Ontario           | `ont`        | `oklch(0.593 0.207 269.4)` | `#4F6EF7` |
| ![](https://placehold.co/16x16/3A9D7A/3A9D7A.png) | Pacific Northwest | `pnw`        | `oklch(0.628 0.107 166.2)` | `#3A9D7A` |
| ![](https://placehold.co/16x16/FDB4A0/FDB4A0.png) | Peachtree         | `pch`        | `oklch(0.834 0.090 35.9)`  | `#FDB4A0` |
| ![](https://placehold.co/16x16/4FA37A/4FA37A.png) | South Carolina    | `fsc`        | `oklch(0.651 0.103 160.3)` | `#4FA37A` |
| ![](https://placehold.co/16x16/E36A2E/E36A2E.png) | Texas             | `fit`, `tx`  | `oklch(0.661 0.167 44.1)`  | `#E36A2E` |
| ![](https://placehold.co/16x16/E84393/E84393.png) | Wisconsin         | `win`        | `oklch(0.643 0.212 355.2)` | `#E84393` |

(All this said, colors are never "final", so be sure to double-check the code to verify this readme is up to date.)

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

1. Put some form of example in `.env.example`
2. Add the environment variable to `app/vite-env.d.ts`
3. Add a validator to `vite.config.ts`
4. You can then reference it in code with `import.env.meta.VITE_MY_VAR`.

## PR Screenshots

PRs that touch `pwa/` files can get before/after screenshots posted as a PR comment (via the `PWA Screenshots` workflow). To request screenshots, add a `## Screenshot Pages` section to your PR description:

```markdown
## Screenshot Pages

- /match/2024mil_f1m2
- /team/254/2024 Team 254 Page
- /gameday
```

Each line is `- /path` optionally followed by a display name. If no pages are listed, the workflow skips screenshot capture.

> **Note:** Screenshots require the `TBA_API_READ_KEY` secret, which is only available for same-repo branches (not fork PRs). Fork PRs will gracefully skip screenshot capture.

## Playwright tests

Playwright (end to end) tests are within `./tests`. Test names with `mobile` in the name will be run on mobile; others will be run on desktop viewports. Note that these are run on the production build, so if you make changes, you should re-build with `pnpm run build`.

```sh
# Installs playwright binaries
pnpm dlx playwright install

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
