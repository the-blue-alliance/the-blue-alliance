import type { Client } from '~/api/tba/read/client';
import { client } from '~/api/tba/read/client.gen';

export type SdkFn = (options: never) => Promise<{ data?: unknown }>;
export type SdkOptions<F extends SdkFn> = Omit<
  NonNullable<Parameters<F>[0]>,
  'body'
>;
export type SdkData<F extends SdkFn> = Exclude<
  Awaited<ReturnType<F>>['data'],
  undefined
>;

const methods = ['get', 'post', 'put', 'patch', 'delete'] as const;

export interface TbaRequest {
  method: (typeof methods)[number];
  path: string;
}

export interface SsrMock {
  method: string;
  path: string;
  body: unknown;
}

export function describeTbaRequest<F extends SdkFn>(
  sdkFn: F,
  options: SdkOptions<F>,
): TbaRequest {
  const described: TbaRequest[] = [];
  const recorder = Object.fromEntries(
    methods.map((method) => [
      method,
      (request: Parameters<Client['buildUrl']>[0]) => {
        const path = client.buildUrl({ ...request, baseUrl: '', query: {} });
        described.push({ method, path });
        return Promise.resolve({});
      },
    ]),
  );
  void sdkFn(
    Object.assign({}, options, { client: recorder }) as Parameters<F>[0],
  );
  return described[0];
}
