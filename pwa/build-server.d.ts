/**
 * Type definitions for the TanStack Start build output.
 * This file provides types for the server handler that's generated during the build process.
 */

declare module '*/build/server/server.js' {
  interface ServerHandler {
    fetch: (request: Request) => Response | Promise<Response>;
  }

  const handler: ServerHandler;
  export default handler;
}
