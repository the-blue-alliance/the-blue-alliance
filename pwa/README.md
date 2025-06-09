# The Blue Alliance PWA (beta)

## Development - Optional

You can optionally use [devbox](https://www.jetify.com/devbox) to set up a reproducible shell. Follow the instructions on the devbox website to install it, then:

```sh
devbox shell
```

to enter a shell with system dependencies preinstalled. Otherwise, you'll need Node v20 (we specifically pin to 20.16, but others will work).

## Development

First install the dependencies:

```shellscript
npm i
```

Make sure you have your TBA APIv3 Read Key set in `.env`:

```sh
$ cp default.env .env
VITE_TBA_API_READ_KEY="myKey"
```

Run the dev server:

```shellscript
npm run dev
```

## Deployment

First, build your app for production:

```sh
npm run build
```

Then run the app in production mode:

```sh
npm start
```

Now you'll need to pick a host to deploy it to.

### DIY

If you're familiar with deploying Node applications, the built-in Remix app server is production-ready.

Make sure to deploy the output of `npm run build`

- `build/server`
- `build/client`

## Styling

This template comes with [Tailwind CSS](https://tailwindcss.com/) already configured for a simple default starting experience. You can use whatever css framework you prefer. See the [Vite docs on css](https://vitejs.dev/guide/features.html#css) for more information.

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

## Playwright tests

Playwright (end to end) tests are within `./tests`. Test names with `mobile` in the name will be run on mobile; others will be run on desktop viewports.

```sh
# Runs the end-to-end tests.
npx playwright test

# Starts the interactive UI mode.
npx playwright test --ui

# Runs the tests only on Desktop Chrome.
npx playwright test --project=chromium

# Runs the tests in a specific file.
npx playwright test example

# Runs the tests in debug mode.
npx playwright test --debug

# Auto generate tests with Codegen.
npx playwright codegen

# Auto generate tests with a specific device
npx playwright codegen --device="Pixel 7"
```

## Auth

Currently, the emulator suite doesn't work; this means you'll have to set up a prod Firebase project and tell the py3 codebase to use it.

1. Go to https://console.firebase.google.com/
2. Create project
3. Enter a project name, such as `tba-dev`
4. Disable Google Analytics, hit Create Project
5. Go to Project Settings
6. Create a web platform App
7. Enter a name, such as `tba-dev`
8. Hit Register app
9. Copy the API key, auth domain, project ID, storage bucket, messaging sender ID, and app ID to `src/backend/web/static/javascript/tba_js/tba_keys.js`. You may need to `chmod` this depending on your local environment and how the file was made.
10. Copy the API key, auth domain, and project ID to `pwa/.env`.
11. Go to Project Settings -> Service Accounts
12. Click `Generate new private key` to download a JSON file
13. Move the json file to `ops/dev/keys/key.json` (specific filename and path do not matter, just an example)
14. From the json file, copy the project ID, client email, and private key to `pwa/.env`.
15. Open `tba_dev_config.json`
16. Add `"auth_use_prod": true` and `"google_application_credentials": "ops/dev/keys/key.json"` (or wherever you put the key file)
17. Run `./ops/build/run_buildweb.sh` to rebuild JS bundles.
18. Go to http://localhost:8080/account/login and Sign in with Google.
19. Go to http://localhost:5173/account and Sign in with Google.
