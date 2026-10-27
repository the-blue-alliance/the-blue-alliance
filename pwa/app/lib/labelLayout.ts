export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface LabelAnchor {
  x: number;
  y: number;
  r: number;
  w: number;
  h: number;
}

const GAP = 2;
const STEPS_PER_LABEL = 400;
const BOUNDS_WEIGHT = 2;
const PREFERENCE_WEIGHT = 0.02;

// The 8 spots a label may take around its dot, in order of preference:
// top first, then top-right, right, and around to bottom-left.
function candidates({ x, y, r, w, h }: LabelAnchor): Box[] {
  const d = r + GAP;
  const k = d * Math.SQRT1_2;
  return [
    { x: x - w / 2, y: y - d - h, w, h },
    { x: x + k, y: y - k - h, w, h },
    { x: x + d, y: y - h / 2, w, h },
    { x: x - k - w, y: y - k - h, w, h },
    { x: x - d - w, y: y - h / 2, w, h },
    { x: x + k, y: y + k, w, h },
    { x: x - w / 2, y: y + d, w, h },
    { x: x - k - w, y: y + k, w, h },
  ];
}

// Area in square pixels where two boxes overlap, or 0 if they don't touch.
function overlap(a: Box, b: Box): number {
  const w = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
  const h = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
  return w > 0 && h > 0 ? w * h : 0;
}

// The square around a dot, used as an obstacle that labels should avoid.
function dotBox({ x, y, r }: LabelAnchor): Box {
  return { x: x - r, y: y - r, w: 2 * r, h: 2 * r };
}

// How bad it is to put label `index` in `box`: how much it covers other labels
// and dots, how far it sticks out of bounds, and a small penalty for less
// preferred spots. Lower is better.
function cost(
  index: number,
  box: Box,
  preference: number,
  labels: Box[],
  dots: Box[],
  bounds: Box,
): number {
  const area = box.w * box.h;
  let covered = 0;
  for (let j = 0; j < labels.length; j++) {
    if (j !== index) covered += overlap(box, labels[j]) + overlap(box, dots[j]);
  }
  const outside = area - overlap(box, bounds);
  return (
    (covered + BOUNDS_WEIGHT * outside) / area + PREFERENCE_WEIGHT * preference
  );
}

// A small seeded random number generator (mulberry32). A fixed seed makes the
// same data always produce the same layout, so labels don't jump between
// renders.
function seededRandom(seed: number): () => number {
  let state = seed;
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Places one label per dot with simulated annealing: try random moves to other
// spots, always keep moves that lower the cost, and early on sometimes keep
// worse ones so the layout doesn't get stuck.
export function layoutLabels(anchors: LabelAnchor[], bounds: Box): Box[] {
  const dots = anchors.map(dotBox);
  const options = anchors.map(candidates);
  const choices = anchors.map(() => 0);
  const labels = options.map((o) => o[0]);
  const random = seededRandom(1);
  const steps = anchors.length * STEPS_PER_LABEL;
  const cooling = Math.pow(0.001, 1 / steps);
  let temperature = 1;
  for (let step = 0; step < steps; step++) {
    const i = Math.floor(random() * anchors.length);
    const next = Math.floor(random() * options[i].length);
    const delta =
      cost(i, options[i][next], next, labels, dots, bounds) -
      cost(i, labels[i], choices[i], labels, dots, bounds);
    if (delta <= 0 || random() < Math.exp(-delta / temperature)) {
      choices[i] = next;
      labels[i] = options[i][next];
    }
    temperature *= cooling;
  }
  return labels;
}
