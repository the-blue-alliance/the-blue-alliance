import { HttpResponse, type HttpResponseResolver, http } from 'msw';
import { setupServer } from 'msw/node';

import type { Client } from '~/api/tba/read/client';
import { client } from '~/api/tba/read/client.gen';

export const server = setupServer();

type SdkFn = (options: never) => Promise<{ data?: unknown }>;
type SdkOptions<F extends SdkFn> = Omit<NonNullable<Parameters<F>[0]>, 'body'>;
type SdkData<F extends SdkFn> = Exclude<
  Awaited<ReturnType<F>>['data'],
  undefined
>;

const methods = ['get', 'post', 'put', 'patch', 'delete'] as const;

export function mockTbaApiWith<F extends SdkFn>(
  sdkFn: F,
  options: SdkOptions<F>,
  resolver: HttpResponseResolver,
) {
  const recorder = Object.fromEntries(
    methods.map((method) => [
      method,
      (request: Parameters<Client['buildUrl']>[0]) => {
        const path = client.buildUrl({ ...request, baseUrl: '', query: {} });
        server.use(http[method](`*${path}`, resolver));
        return Promise.resolve({});
      },
    ]),
  );
  void sdkFn(
    Object.assign({}, options, { client: recorder }) as Parameters<F>[0],
  );
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
