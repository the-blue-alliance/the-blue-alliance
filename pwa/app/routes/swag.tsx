import { createFileRoute, redirect } from '@tanstack/react-router';

const SWAG_URL =
  'https://www.amazon.com/s/ref=w_bl_sl_s_ap_web_7141123011?ie=UTF8&node=7141123011&field-brandtextbin=The+Blue+Alliance';

export const Route = createFileRoute('/swag')({
  beforeLoad: () => {
    throw redirect({ href: SWAG_URL, statusCode: 302 });
  },
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop
