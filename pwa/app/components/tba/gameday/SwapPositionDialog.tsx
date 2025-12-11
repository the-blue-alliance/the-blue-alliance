import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog';
import { useGameday } from '~/lib/gameday/context';
import { getLayoutById } from '~/lib/gameday/layouts';

function SwapPositionPreviewCell({
  gridArea,
  enabled,
  onClick,
}: {
  gridArea: string;
  enabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      style={{ gridArea }}
      className={
        'm-1 rounded transition-colors ' +
        (enabled
          ? 'cursor-pointer bg-neutral-300 hover:bg-neutral-400'
          : 'cursor-default bg-neutral-600')
      }
      onClick={enabled ? onClick : undefined}
      disabled={!enabled}
    />
  );
}

export function SwapPositionDialog({
  open,
  onOpenChange,
  currentPosition,
  onPositionSelected,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentPosition: number;
  onPositionSelected: (position: number) => void;
}) {
  const { state } = useGameday();

  const layout = getLayoutById(state.layoutId);
  if (!layout) return null;

  const cells = layout.gridAreas.map((area, i) => (
    <SwapPositionPreviewCell
      key={i}
      gridArea={area}
      enabled={i !== currentPosition}
      onClick={() => onPositionSelected(i)}
    />
  ));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        onOpenAutoFocus={(e) => {
          e.preventDefault();
          (e.currentTarget as HTMLElement)?.focus();
        }}
        className="max-w-md p-0"
      >
        <DialogHeader className="border-b px-4 py-3">
          <DialogTitle>Select a position to swap with</DialogTitle>
        </DialogHeader>
        <div className="p-4">
          <div
            className="grid aspect-video"
            style={{ gridTemplate: layout.gridTemplate }}
          >
            {cells}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
