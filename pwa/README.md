# Welcome to Remix!

- 📖 [Remix docs](https://remix.run/docs)

## Development

First install the dependencies:

```shellscript
npm i
```

Make sure you have your TBA APIv3 Read Key set in `.env`:

```sh
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
