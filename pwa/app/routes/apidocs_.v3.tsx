import type { MetaFunction } from 'react-router';

import { ApiDocsFrame } from '~/components/tba/api/ApiDocsFrame';

export const meta: MetaFunction = () => {
  return [{ title: 'APIv3 Docs - The Blue Alliance' }];
};

export default function ApiDocsRoute() {
  return <ApiDocsFrame url={'/swagger/api/v3'} />;
}
