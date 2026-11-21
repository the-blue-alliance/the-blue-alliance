import { HttpResponse, type HttpResponseResolver, http } from 'msw';
import { setupServer } from 'msw/node';

import {
  type SdkData,
  type SdkFn,
  type SdkOptions,
  describeTbaRequest,
} from '~/test/tbaRequest';

export const server = setupServer();

export function mockTbaApiWith<F extends SdkFn>(
  sdkFn: F,
  options: SdkOptions<F>,
  resolver: HttpResponseResolver,
) {
  const { method, path } = describeTbaRequest(sdkFn, options);
  server.use(http[method](`*${path}`, resolver));
}

export function mockTbaApi<F extends SdkFn>(
  sdkFn: F,
  options: SdkOptions<F>,
  body: SdkData<F>,
) {
  const requests: Request[] = [];
  mockTbaApiWith(sdkFn, options, ({ request }) => {
    requests.push(request);
    return HttpResponse.json(body);
  });
  return requests;
}
