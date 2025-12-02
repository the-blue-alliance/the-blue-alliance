import SwaggerUI from 'swagger-ui-react';
import 'swagger-ui-react/swagger-ui.css';

export function ApiDocsFrame({ url }: { url: string }) {
  return <SwaggerUI url={url} />;
}
