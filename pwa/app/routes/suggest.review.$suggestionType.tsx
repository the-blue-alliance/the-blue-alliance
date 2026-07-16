import { Link, createFileRoute, notFound } from '@tanstack/react-router';
import { type JSX, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

import type {
  AcceptRequest,
  ModerationSuggestion,
  SuggestionType,
} from '~/api/tba/moderation/types.gen';
import { useAuth } from '~/components/tba/auth/auth';
import LoginPage from '~/components/tba/auth/loginPage';
import { KeyboardShortcutsDialog } from '~/components/tba/moderation/keyboardShortcutsDialog';
import { ReviewGuidelines } from '~/components/tba/moderation/reviewGuidelines';
import {
  type ReviewDecision,
  SuggestionReviewCard,
} from '~/components/tba/moderation/suggestionReviewCard';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '~/components/ui/breadcrumb';
import { Button } from '~/components/ui/button';
import { Spinner } from '~/components/ui/spinner';
import {
  useModerationSuggestions,
  useReviewSubmission,
} from '~/lib/hooks/useModeration';
import {
  defaultSetPreferred,
  formatEventDateRange,
  groupSuggestionsByTargetKey,
  summarizeReviewOutcomes,
} from '~/lib/moderationUtils';

const TYPE_NAMES: Record<SuggestionType, string> = {
  event: 'Webcasts',
  match: 'Match Videos',
  media: 'Team Media',
  'social-media': 'Social Media',
  'offseason-event': 'Offseason Events',
  api_auth_access: 'API Key Requests',
  robot: 'CAD Models',
  event_media: 'Event Videos',
};

function WebcastEventGroup({
  group,
  onRejectAll,
  children,
}: {
  group: { targetKey: string; suggestions: ModerationSuggestion[] };
  onRejectAll: () => void;
  children: React.ReactNode;
}): JSX.Element {
  const first = group.suggestions[0];
  const event = first.event;
  const dates = formatEventDateRange(event?.start_date, event?.end_date);
  const existingWebcasts = first.existing_webcasts ?? [];
  return (
    <section className="flex flex-col gap-3 rounded-lg border bg-muted/30 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-medium">
          {event ? (
            <Link
              to="/event/$eventKey"
              params={{ eventKey: event.key }}
              className="text-primary underline underline-offset-2"
            >
              {event.year} {event.name} ({event.key})
            </Link>
          ) : (
            group.targetKey
          )}
          {dates && (
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              {dates}
            </span>
          )}
        </h2>
        <Button
          variant="outline"
          size="sm"
          className="hover:text-destructive-foreground hover:bg-destructive"
          onClick={onRejectAll}
        >
          Reject All
        </Button>
      </div>
      <div className="text-sm">
        <span className="font-medium text-muted-foreground">
          Existing webcasts:
        </span>{' '}
        {existingWebcasts.length > 0
          ? existingWebcasts
              .map((webcast) =>
                [webcast.type, webcast.channel, webcast.file]
                  .filter(Boolean)
                  .join(' / '),
              )
              .join(', ')
          : 'None yet!'}
      </div>
      {children}
    </section>
  );
}

export const Route = createFileRoute('/suggest/review/$suggestionType')({
  params: {
    parse: (params) => {
      if (!(params.suggestionType in TYPE_NAMES)) {
        throw notFound();
      }
      return { suggestionType: params.suggestionType as SuggestionType };
    },
  },
  component: SuggestionReviewList,
});

function SuggestionReviewList(): JSX.Element {
  const { suggestionType } = Route.useParams();
  const { isInitialLoading, user } = useAuth();
  const { data, isLoading, error } = useModerationSuggestions(suggestionType);
  const submission = useReviewSubmission(suggestionType);

  const [decisions, setDecisions] = useState<Record<string, ReviewDecision>>(
    {},
  );
  const [overrides, setOverrides] = useState<Record<string, AcceptRequest>>({});
  const [focusedKey, setFocusedKey] = useState<string | null>(null);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  // Cards in visual order (webcasts render grouped by event), for j/k
  const orderedSuggestions = useMemo(() => {
    const loaded = data?.suggestions ?? [];
    return suggestionType === 'event'
      ? groupSuggestionsByTargetKey(loaded).flatMap(
          (group) => group.suggestions,
        )
      : loaded;
  }, [data, suggestionType]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target as HTMLElement | null;
      if (
        target?.closest('input, textarea, select, [contenteditable="true"]')
      ) {
        return;
      }
      if (e.key === '?') {
        e.preventDefault();
        setShortcutsOpen((open) => !open);
        return;
      }
      if (shortcutsOpen || orderedSuggestions.length === 0) return;

      const keys = orderedSuggestions.map((s) => s.key);
      const focusedIndex = focusedKey ? keys.indexOf(focusedKey) : -1;

      if (e.key === 'j' || e.key === 'k') {
        e.preventDefault();
        const nextIndex =
          e.key === 'j'
            ? Math.min(focusedIndex + 1, keys.length - 1)
            : Math.max(focusedIndex - 1, 0);
        const nextKey = keys[nextIndex];
        setFocusedKey(nextKey);
        document
          .querySelector(`[data-testid="suggestion-${nextKey}"]`)
          ?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
      }

      const focusedSuggestion =
        focusedIndex >= 0 ? orderedSuggestions[focusedIndex] : undefined;
      if (!focusedSuggestion) return;

      if (e.key === 'a' || e.key === 'r') {
        e.preventDefault();
        const decision = e.key === 'a' ? 'accept' : 'reject';
        setDecisions((prev) => ({
          ...prev,
          [focusedSuggestion.key]:
            prev[focusedSuggestion.key] === decision ? undefined : decision,
        }));
      } else if (
        e.key === 'p' &&
        suggestionType === 'media' &&
        focusedSuggestion.candidate_media?.is_image
      ) {
        e.preventDefault();
        setOverrides((prev) => {
          const current =
            prev[focusedSuggestion.key]?.set_preferred ??
            defaultSetPreferred(focusedSuggestion);
          return {
            ...prev,
            [focusedSuggestion.key]: {
              ...(prev[focusedSuggestion.key] ?? {}),
              set_preferred: !current,
            },
          };
        });
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [orderedSuggestions, focusedKey, shortcutsOpen, suggestionType]);

  if (isInitialLoading) {
    return <Spinner className="mx-auto mt-16" />;
  }
  if (!user) {
    return <LoginPage />;
  }
  if (error) {
    return (
      <div className="mx-auto mt-16 max-w-lg text-center">
        <h1 className="text-2xl font-semibold">{TYPE_NAMES[suggestionType]}</h1>
        <p className="mt-4 text-muted-foreground">
          You do not have permission to review {TYPE_NAMES[suggestionType]}{' '}
          suggestions. If this is incorrect, please contact the TBA admins.
        </p>
      </div>
    );
  }
  if (isLoading || !data) {
    return <Spinner className="mx-auto mt-16" />;
  }

  const suggestions = data.suggestions;
  const setAll = (decision: ReviewDecision) => {
    setDecisions(Object.fromEntries(suggestions.map((s) => [s.key, decision])));
  };
  const decidedCount = suggestions.filter((s) => decisions[s.key]).length;

  const submit = () => {
    const accepts = suggestions
      .filter((s) => decisions[s.key] === 'accept')
      .map((s) => {
        const acceptOverrides = { ...(overrides[s.key] ?? {}) };
        // The preferred checkbox shows a computed default; send it explicitly
        // when the moderator didn't touch it
        if (
          suggestionType === 'media' &&
          acceptOverrides.set_preferred === undefined
        ) {
          acceptOverrides.set_preferred = defaultSetPreferred(s);
        }
        return { key: s.key, overrides: acceptOverrides };
      });
    const rejects = suggestions
      .filter((s) => decisions[s.key] === 'reject')
      .map((s) => s.key);
    submission.mutate(
      { accepts, rejects },
      {
        onSuccess: (result) => {
          const summary = summarizeReviewOutcomes(result);
          if (summary) {
            const processed =
              result.accepted.length +
              result.rejected.length +
              result.alreadyReviewed.length;
            const remaining = (data?.total ?? suggestions.length) - processed;
            if (remaining <= 0 && result.failed.length === 0) {
              toast.success(`Queue cleared! 🎉 ${summary}`, { duration: 6000 });
            } else {
              toast.success(summary);
            }
          }
          for (const failure of result.failed) {
            toast.error(`${failure.key}: ${failure.message}`);
          }
          setDecisions({});
          setOverrides({});
        },
        onError: (submissionError) => {
          toast.error(`Review submission failed: ${submissionError.message}`);
        },
      },
    );
  };

  const renderCard = (
    suggestion: (typeof suggestions)[number],
    hideEventContext?: boolean,
  ): JSX.Element => (
    <SuggestionReviewCard
      key={suggestion.key}
      suggestion={suggestion}
      decision={decisions[suggestion.key]}
      onDecisionChange={(decision) =>
        setDecisions((prev) => ({
          ...prev,
          [suggestion.key]: decision,
        }))
      }
      overrides={overrides[suggestion.key] ?? {}}
      onOverridesChange={(next) =>
        setOverrides((prev) => ({ ...prev, [suggestion.key]: next }))
      }
      hideEventContext={hideEventContext}
      focused={focusedKey === suggestion.key}
    />
  );

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4 p-4">
      <div>
        <Breadcrumb className="mb-1">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink render={<Link to="/suggest/review" />}>
                Suggestions
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{TYPE_NAMES[suggestionType]}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-semibold">
          Review: {TYPE_NAMES[suggestionType]}
        </h1>
        <p className="text-muted-foreground">
          {data.total > suggestions.length
            ? `Showing the first ${suggestions.length} of ${data.total} pending suggestions`
            : `${suggestions.length} pending suggestion${suggestions.length === 1 ? '' : 's'}`}
        </p>
      </div>

      <ReviewGuidelines suggestionType={suggestionType} />

      {suggestions.length === 0 ? (
        <p className="mt-8 text-center text-muted-foreground">
          Nothing to review — the queue is empty. 🎉
        </p>
      ) : (
        <>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              className="hover:bg-green-700 hover:text-white"
              onClick={() => setAll('accept')}
            >
              Select All Accepts
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="hover:text-destructive-foreground hover:bg-destructive"
              onClick={() => setAll('reject')}
            >
              Select All Rejects
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAll(undefined)}
            >
              Deselect All
            </Button>
            <button
              type="button"
              className="ml-auto text-sm text-primary underline
                underline-offset-2"
              onClick={() => setShortcutsOpen(true)}
            >
              see keyboard shortcuts (?)
            </button>
          </div>

          <div className="flex flex-col gap-4">
            {suggestionType === 'event'
              ? groupSuggestionsByTargetKey(suggestions).map((group) => (
                  <WebcastEventGroup
                    key={group.targetKey}
                    group={group}
                    onRejectAll={() =>
                      setDecisions((prev) => ({
                        ...prev,
                        ...Object.fromEntries(
                          group.suggestions.map((s) => [s.key, 'reject']),
                        ),
                      }))
                    }
                  >
                    {group.suggestions.map((suggestion) =>
                      renderCard(suggestion, true),
                    )}
                  </WebcastEventGroup>
                ))
              : suggestions.map((suggestion) => renderCard(suggestion))}
          </div>

          <div className="sticky bottom-4 flex justify-end">
            <Button
              onClick={submit}
              disabled={decidedCount === 0 || submission.isPending}
              className="shadow-lg"
              data-testid="submit-review"
            >
              {submission.isPending ? <Spinner className="mr-2" /> : null}
              Act on {decidedCount} Selected
            </Button>
          </div>
        </>
      )}
      <KeyboardShortcutsDialog
        open={shortcutsOpen}
        onOpenChange={setShortcutsOpen}
      />
    </div>
  );
}
