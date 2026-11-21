import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  addWebhook,
  deleteWebhook,
  listWebhooks,
  pingMobileClient,
  sendWebhookTest,
  sendWebhookVerification,
  verifyWebhook,
} from '~/api/tba/mobile/sdk.gen';
import type {
  BaseResponse,
  ListWebhooksResponse,
  SendWebhookTestData,
  Webhook,
} from '~/api/tba/mobile/types.gen';
import { useAuth } from '~/components/tba/auth/auth';

function assertOk(response: { data?: BaseResponse }, fallback: string) {
  if (response.data?.code !== 200) {
    throw new Error(response.data?.message ?? fallback);
  }
}

export function useWebhooks() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const queryKey = ['webhooks', user?.uid];

  const getToken = async () => {
    if (!user) throw new Error('User not authenticated');
    return user.getIdToken();
  };

  const updateWebhooks = (update: (webhooks: Webhook[]) => Webhook[]) => {
    queryClient.setQueryData<ListWebhooksResponse>(queryKey, (old) => ({
      ...old,
      webhooks: update(old?.webhooks ?? []),
    }));
  };

  const query = useQuery({
    queryKey,
    queryFn: async () => {
      const response = await listWebhooks({ auth: await getToken() });
      if (response.data === undefined) {
        throw new Error('Failed to load webhooks');
      }
      return response.data;
    },
    enabled: !!user,
  });

  const addMutation = useMutation({
    mutationFn: async (body: { name: string; url: string }) => {
      const response = await addWebhook({ auth: await getToken(), body });
      assertOk(response, 'Failed to add webhook');
      const webhook = response.data?.webhook;
      if (!webhook) throw new Error('Failed to add webhook');
      return webhook;
    },
    onSuccess: (webhook) => {
      updateWebhooks((webhooks) => [
        ...webhooks.filter((w) => w.webhook_id !== webhook.webhook_id),
        webhook,
      ]);
    },
  });

  const verifyMutation = useMutation({
    mutationFn: async (body: { webhook_id: string; code: string }) => {
      const response = await verifyWebhook({ auth: await getToken(), body });
      assertOk(response, 'Failed to verify webhook');
      return body.webhook_id;
    },
    onSuccess: (webhookId) => {
      updateWebhooks((webhooks) =>
        webhooks.map((w) =>
          w.webhook_id === webhookId ? { ...w, verified: true } : w,
        ),
      );
    },
  });

  const resendMutation = useMutation({
    mutationFn: async (webhookId: string) => {
      const response = await sendWebhookVerification({
        auth: await getToken(),
        body: { webhook_id: webhookId },
      });
      assertOk(response, 'Failed to send a new code');
      return webhookId;
    },
    onSuccess: (webhookId) => {
      updateWebhooks((webhooks) =>
        webhooks.map((w) =>
          w.webhook_id === webhookId ? { ...w, verified: false } : w,
        ),
      );
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (webhookId: string) => {
      const response = await deleteWebhook({
        auth: await getToken(),
        body: { webhook_id: webhookId },
      });
      assertOk(response, 'Failed to delete webhook');
      return webhookId;
    },
    onSuccess: (webhookId) => {
      updateWebhooks((webhooks) =>
        webhooks.filter((w) => w.webhook_id !== webhookId),
      );
    },
  });

  const pingMutation = useMutation({
    mutationFn: async (url: string) => {
      const response = await pingMobileClient({
        auth: await getToken(),
        body: { mobile_id: url },
      });
      assertOk(response, 'Failed to send ping');
    },
  });

  const testMutation = useMutation({
    mutationFn: async (body: SendWebhookTestData['body']) => {
      const response = await sendWebhookTest({ auth: await getToken(), body });
      assertOk(response, 'Failed to send test notification');
    },
  });

  return {
    webhooks: query.data?.webhooks ?? [],
    isLoading: query.isLoading,
    addWebhook: addMutation.mutateAsync,
    verifyWebhook: verifyMutation.mutateAsync,
    resendVerification: resendMutation.mutateAsync,
    deleteWebhook: deleteMutation.mutateAsync,
    pingWebhook: pingMutation.mutateAsync,
    sendTest: testMutation.mutateAsync,
  };
}
