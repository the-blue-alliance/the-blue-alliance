import { type ReactNode, useState } from 'react';

import type { ModelType, NotificationType } from '~/api/tba/mobile/types.gen';
import { Button } from '~/components/ui/button';
import { Checkbox } from '~/components/ui/checkbox';
import {
  Credenza,
  CredenzaBody,
  CredenzaClose,
  CredenzaContent,
  CredenzaDescription,
  CredenzaFooter,
  CredenzaHeader,
  CredenzaTitle,
  CredenzaTrigger,
} from '~/components/ui/credenza';
import { useMyTBA } from '~/lib/hooks/useMyTBA';
import {
  SUBSCRIPTION_TYPES,
  SUBSCRIPTION_TYPE_DISPLAY_NAMES,
} from '~/lib/myTBAConstants';

interface PreferencesDialogProps {
  modelKey: string;
  modelType: ModelType;
  trigger: ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export default function PreferencesDialog({
  modelKey,
  modelType,
  trigger,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
}: PreferencesDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : internalOpen;
  const onOpenChange = isControlled ? controlledOnOpenChange : setInternalOpen;

  return (
    <Credenza open={open} onOpenChange={onOpenChange}>
      <CredenzaTrigger asChild>{trigger}</CredenzaTrigger>
      <CredenzaContent>
        <CredenzaHeader>
          <CredenzaTitle>Preferences for {modelKey}</CredenzaTitle>
          <CredenzaDescription>
            Manage your favorite status and notification subscriptions.
          </CredenzaDescription>
        </CredenzaHeader>
        {open && (
          <PreferencesForm
            modelKey={modelKey}
            modelType={modelType}
            onClose={() => onOpenChange?.(false)}
          />
        )}
      </CredenzaContent>
    </Credenza>
  );
}

function PreferencesForm({
  modelKey,
  modelType,
  onClose,
}: {
  modelKey: string;
  modelType: ModelType;
  onClose: () => void;
}) {
  const { isFavorite, notifications, setPreferences, isPending } = useMyTBA(
    modelKey,
    modelType,
  );

  const [localFavorite, setLocalFavorite] = useState(isFavorite);
  const [localNotifications, setLocalNotifications] = useState<
    Set<NotificationType>
  >(new Set(notifications));

  const handleSave = () => {
    setPreferences(localFavorite, Array.from(localNotifications));
    onClose();
  };

  const toggleNotification = (type: NotificationType) => {
    setLocalNotifications((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  return (
    <>
      <CredenzaBody>
        <div className="space-y-4 py-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="favorite"
              checked={localFavorite}
              onCheckedChange={(checked) => setLocalFavorite(checked === true)}
            />
            <label htmlFor="favorite" className="text-sm font-medium">
              Favorite
            </label>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Notifications</p>
            {SUBSCRIPTION_TYPES.map((type) => (
              <div key={type} className="flex items-center space-x-2">
                <Checkbox
                  id={`notif-${type}`}
                  checked={localNotifications.has(type)}
                  onCheckedChange={() => toggleNotification(type)}
                />
                <label
                  htmlFor={`notif-${type}`}
                  className="text-sm font-medium"
                >
                  {SUBSCRIPTION_TYPE_DISPLAY_NAMES[type]}
                </label>
              </div>
            ))}
          </div>
        </div>
      </CredenzaBody>
      <CredenzaFooter>
        <CredenzaClose asChild>
          <Button variant="outline">Cancel</Button>
        </CredenzaClose>
        <Button onClick={handleSave} disabled={isPending}>
          Save
        </Button>
      </CredenzaFooter>
    </>
  );
}
