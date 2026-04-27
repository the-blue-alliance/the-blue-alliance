# FRCStats → TBA PWA: District Championship Tracking Page Migration Plan

## Overview

Port the district championship live-tracking feature from [frc.jmiller.dev](https://frc.jmiller.dev/) (FRCStats) into the TBA PWA at the route `/district/{district_key}/tracking`.

**Current status:** Research complete, implementation in progress.

---

## Route

`/district/$districtAbbreviation/tracking`
New file: `pwa/app/routes/district.$districtAbbreviation.tracking.tsx`

Sibling routes for reference: `stats`, `insights`, `{-$year}`

---

## Feature Summary

A live-tracking page that shows district teams' performance at the FIRST Championship (CMP). The page auto-refreshes every 60 seconds and displays:

- Per-division match tables with team color coding
- Per-division rankings tables (filtered to district teams only)
- An "All Matches" combined tab
- Subtle auto-refresh countdown badge

---

## Decisions (Resolved)

### 1. Division Discovery

**Decision:** Dynamically query TBA via `getEventsByYearOptions({ path: { year: 2026 } })` and filter by `event_type === EventType.CMP_DIVISION` (= `3`). The current year is always assumed to be `2026`.

### 2. All-Matches Tab

**Decision:** Include as a **third tab** alongside per-division tabs. Tab order: Division tabs first, then "All Matches".

### 3. Statbotics Links

**Decision:** **Include** Statbotics links alongside TBA links for each team. Format:

- TBA: `https://www.thebluealliance.com/team/{number}`
- Statbotics: `https://www.statbotics.io/team/{number}`

### 4. Auto-Refresh Countdown Display

**Decision:** Show a **subtle** "auto-refresh in Xs" countdown badge. No flashy animations. A small muted badge that counts down from 60 to 0.

### 5. Color Fallback When frc-colors Unavailable

**Decision:** Fall back to **red/blue alliance cell backgrounds** (i.e., standard red/blue coloring) when frc-colors data is unavailable for a team.

### 6. Navigation / Discovery

**Decision:** Add a `"Follow teams at FIRST Championship"` text/link in the **district page header**, between the `<h1>{name} {year}</h1>` heading and the year `<Select>` dropdown.
File to edit: `pwa/app/routes/district.$districtAbbreviation.{-$year}.tsx`

---

## Files to Create / Edit

| File                                                         | Action     | Notes                                                            |
| ------------------------------------------------------------ | ---------- | ---------------------------------------------------------------- |
| `pwa/app/routes/district.$districtAbbreviation.tracking.tsx` | **Create** | New route — primary deliverable                                  |
| `pwa/app/routes/district.$districtAbbreviation.{-$year}.tsx` | **Edit**   | Add "Follow teams at FIRST Championship" link in header          |
| `pwa/app/routeTree.gen.ts`                                   | **Edit**   | Register new tracking route (follows `stats`/`insights` pattern) |

---

## Technical Stack

| Concern             | Solution                                                                                     |
| ------------------- | -------------------------------------------------------------------------------------------- |
| Routing             | TanStack Router (file-based)                                                                 |
| Data fetching       | TanStack React Query (`useQuery`, `useQueries`)                                              |
| Auto-refresh        | `refetchInterval: 60_000` on all queries                                                     |
| Live data in loader | None — live data is client-side only; loader only fetches static metadata for `<head>` title |
| Team colors         | frc-colors API via `getEventColors` from `~/api/colors`                                      |
| Color fallback      | Red/blue alliance background per team                                                        |
| Countdown badge     | `useEffect` + `setInterval` (60→0 countdown, resets on `isFetching`)                         |

---

## Data Flow

```
1. loader (static)
   └── getDistrictHistory → district display name for <head> title

2. Component (client-side, refetchInterval: 60_000)
   ├── getDistrictTeamsKeys({ districtKey }) → Set<string> of district team keys
   ├── getEventsByYear({ year: 2026 })
   │     └── filter by event_type === EventType.CMP_DIVISION (3)
   │     └── → array of CMP division Event objects
   │
   └── For each division (via useQueries):
         ├── getEventMatches({ eventKey })    → Match[]
         ├── getEventRankings({ eventKey })   → EventRanking
         └── getEventColors({ eventKey })     → EventColors (frc-colors API)
```

---

## UI Structure

```
Page Title: "{District Name} — FIRST Championship Tracking"
Subtitle: "Auto-refresh in Xs" (subtle badge)

[Tab: Division 1 Name] [Tab: Division 2 Name] ... [Tab: All Matches]

Per-division tab:
  Matches Table (filtered to district teams only):
    | Match | Red 1 | Red 2 | Red 3 | Red Score | Blue Score | Blue 1 | Blue 2 | Blue 3 |
    - Team cells colored with frc-colors primary color (fallback: red/blue alliance)
    - Text contrast via YIQ formula
    - Each team: TBA link + Statbotics link
    - Match label: "qm5" for quals, "sf1-2" style for elims

  Rankings Table (filtered to district teams only):
    | Rank | Team | W-L-T | RP |

All Matches tab:
  Combined match table from all divisions (same format as per-division)
```

---

## Key Types / APIs

### TBA Types (from `types.gen.ts`)

- `EventType.CMP_DIVISION = 3`
- `AllianceColor.RED = 'red'`, `.BLUE = 'blue'`, `.NO_ALLIANCE = ''`
- `CompLevel`: `QM = 'qm'`, `EF = 'ef'`, `QF = 'qf'`, `SF = 'sf'`, `F = 'f'`
- `Match`: `alliances.red/blue: MatchAlliance`, `winning_alliance: AllianceColor`, `comp_level: CompLevel`, `set_number: number`, `match_number: number`, `time: number|null`, `score_breakdown: MatchScoreBreakdown2026 | ... | null`
- `MatchAlliance`: `team_keys: string[]`, `score: number|null`, `dq_team_keys: string[]`, `surrogate_team_keys: string[]`
- `EventRanking.rankings[]`: `rank`, `team_key`, `matches_played`, `record: WltRecord|null`, `dq`
- `MatchScoreBreakdown2026Alliance`: `totalPoints`, `rp` (plus all 2026-specific fields)

### React Query Option Functions (from `react-query.gen.ts`)

- `getDistrictHistoryOptions({ path: { districtAbbreviation } })` — loader only
- `getDistrictTeamsKeysOptions({ path: { districtKey } })` — district team set
- `getEventsByYearOptions({ path: { year } })` — find CMP divisions
- `getEventMatchesOptions({ path: { eventKey } })` — per-division matches
- `getEventRankingsOptions({ path: { eventKey } })` — per-division rankings

### frc-colors API (from `~/api/colors`)

- `getEventColors({ eventKey })` → `Promise<{status:200, data: EventColors} | {status:500}>`
- `EventColors.teams: Record<string, TeamWithColor>`
- `TeamWithColor.colors: TeamColors | null`
- `TeamColors`: `primaryHex`, `secondaryHex`, `verified: boolean`

---

## Color Logic

```ts
// YIQ contrast formula for text color on colored background
function getTextColor(hex: string): 'black' | 'white' {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return (r * 299 + g * 587 + b * 114) / 1000 >= 128 ? 'black' : 'white';
}

// Priority:
// 1. frc-colors verified → primaryHex bg, secondaryHex outline
// 2. frc-colors unverified → primaryHex bg only
// 3. No colors data → red/blue alliance color fallback
```

---

## Match Label Format

| `comp_level` | `set_number` | `match_number` | Label   |
| ------------ | ------------ | -------------- | ------- |
| `qm`         | —            | 5              | `qm5`   |
| `sf`         | 1            | 2              | `sf1-2` |
| `f`          | 1            | 1              | `f1-1`  |

---

## Header Edit (district `{-$year}` page)

In `district.$districtAbbreviation.{-$year}.tsx`, inside:

```tsx
<div className="mt-4 flex items-center justify-between gap-4">
  <h1>...</h1>
  {/* ADD LINK HERE */}
  <Select>...</Select>
</div>
```

Add:

```tsx
<Link
  to="/district/$districtAbbreviation/tracking"
  params={{ districtAbbreviation }}
  className="text-sm text-muted-foreground hover:text-foreground"
>
  Follow teams at FIRST Championship
</Link>
```

---

## routeTree.gen.ts Changes

Follow the exact pattern of `DistrictDistrictAbbreviationStatsRoute` and `DistrictDistrictAbbreviationInsightsRoute`:

1. Add import:
   ```ts
   import { Route as DistrictDistrictAbbreviationTrackingRouteImport } from './routes/district.$districtAbbreviation.tracking';
   ```
2. Add to all `FileRoutesByPath` interface maps:
   ```ts
   '/district/$districtAbbreviation/tracking': typeof DistrictDistrictAbbreviationTrackingRoute
   ```
3. Add to `DistrictDistrictAbbreviationRouteChildren` and `rootRouteChildren`

---

## Implementation Progress

- [x] FRCStats source analyzed
- [x] PWA routing structure mapped
- [x] All TBA API option functions confirmed
- [x] All relevant TypeScript types confirmed
- [x] `getEventColors` usage pattern confirmed
- [x] `useQuery`/`useQueries` patterns confirmed
- [ ] Create `district.$districtAbbreviation.tracking.tsx`
- [ ] Edit `district.$districtAbbreviation.{-$year}.tsx` header
- [ ] Update `routeTree.gen.ts`
