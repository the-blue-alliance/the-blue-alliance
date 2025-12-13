import { LayoutIcon } from '~/components/tba/gameday/LayoutIcon';
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card';
import { useGameday } from '~/lib/gameday/context';
import { LAYOUT_DISPLAY_ORDER, getLayoutById } from '~/lib/gameday/layouts';

export function LayoutSelector() {
  const { setLayout } = useGameday();

  return (
    <div className="flex h-full w-full items-start justify-center p-4 pt-8">
      <Card className="w-full max-w-md">
        <CardHeader className="pb-2">
          <CardTitle className="text-center text-xl">Select a layout</CardTitle>
        </CardHeader>
        <CardContent className="max-h-[60vh] overflow-y-auto">
          <div className="space-y-1">
            {LAYOUT_DISPLAY_ORDER.map((layoutId) => {
              const layout = getLayoutById(layoutId);
              if (!layout) return null;

              return (
                <button
                  key={layoutId}
                  onClick={() => setLayout(layoutId)}
                  className="flex w-full cursor-pointer items-center
                    justify-between rounded-md px-3 py-2 text-left
                    transition-colors hover:bg-accent"
                >
                  <span className="font-medium">{layout.name}</span>
                  <LayoutIcon layoutId={layoutId} className="h-6 w-10" />
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
