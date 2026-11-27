import FirebaseMirror, { FIREBASE_MIRROR_VALUE } from "../firebaseMirror";

function makeRef() {
  const listeners = {};
  const ref = {
    child: jest.fn((path) => ({
      on: jest.fn((event, cb) => {
        listeners[path] = { event, cb };
      }),
    })),
  };
  return { ref, listeners };
}

function snapshot(value) {
  return { val: () => value };
}

describe("FirebaseMirror", () => {
  it("keeps the ref it was given and starts with nothing watched", () => {
    const { ref } = makeRef();
    const firebaseMirror = new FirebaseMirror({ ref });
    expect(firebaseMirror.ref).toBe(ref);
    expect(firebaseMirror.watching).toEqual({});
    expect(firebaseMirror.dispatch).toBeNull();
  });

  it("subscribes to value events and dispatches each snapshot's value", () => {
    const { ref, listeners } = makeRef();
    const firebaseMirror = new FirebaseMirror({ ref });
    firebaseMirror.dispatch = jest.fn();

    firebaseMirror.watch("e/2024casj/m");

    expect(ref.child).toHaveBeenCalledWith("e/2024casj/m");
    expect(listeners["e/2024casj/m"].event).toBe("value");
    expect(firebaseMirror.watching["e/2024casj/m"]).toBe(true);

    listeners["e/2024casj/m"].cb(snapshot({ qm1: { c: "qm" } }));
    expect(firebaseMirror.dispatch).toHaveBeenCalledWith({
      type: FIREBASE_MIRROR_VALUE,
      path: "e/2024casj/m",
      value: { qm1: { c: "qm" } },
    });
  });

  it("uses the dispatch assigned after watch() was called", () => {
    const { ref, listeners } = makeRef();
    const firebaseMirror = new FirebaseMirror({ ref });
    firebaseMirror.watch("le/2024casj");
    firebaseMirror.dispatch = jest.fn();

    listeners["le/2024casj"].cb(snapshot(null));
    expect(firebaseMirror.dispatch).toHaveBeenCalledWith({
      type: FIREBASE_MIRROR_VALUE,
      path: "le/2024casj",
      value: null,
    });
  });

  it("does not subscribe twice to a path it is already watching", () => {
    const { ref } = makeRef();
    const firebaseMirror = new FirebaseMirror({ ref });
    firebaseMirror.watch("le/2024casj");
    firebaseMirror.watch("le/2024casj");
    expect(ref.child).toHaveBeenCalledTimes(1);
  });

  it("subscribes again after watching[path] is reset to false", () => {
    const { ref } = makeRef();
    const firebaseMirror = new FirebaseMirror({ ref });
    firebaseMirror.watch("le/2024casj");
    firebaseMirror.watching["le/2024casj"] = false;
    firebaseMirror.watch("le/2024casj");
    expect(ref.child).toHaveBeenCalledTimes(2);
  });

  describe("reducer", () => {
    const reducer = new FirebaseMirror({ ref: makeRef().ref }).reducer();
    const watched = (path, value) => ({
      type: FIREBASE_MIRROR_VALUE,
      path,
      value,
    });

    it("starts with empty data", () => {
      expect(reducer(undefined, { type: "@@INIT" })).toEqual({ data: {} });
    });

    it("returns the same state for unrelated actions", () => {
      const state = { data: { e: {} } };
      expect(reducer(state, { type: "OTHER" })).toBe(state);
    });

    it("stores the value at the nested path, creating parents", () => {
      const state = reducer(undefined, watched("e/2024casj/m", { qm1: 1 }));
      expect(state).toEqual({ data: { e: { "2024casj": { m: { qm1: 1 } } } } });
    });

    it("replaces the value at the path rather than merging into it", () => {
      let state = reducer(undefined, watched("le/2024casj", { a: 1, b: 2 }));
      state = reducer(state, watched("le/2024casj", { a: 3 }));
      expect(state.data.le["2024casj"]).toEqual({ a: 3 });
    });

    it("keeps sibling paths and leaves the previous state untouched", () => {
      const before = reducer(undefined, watched("e/2024casj/m", { qm1: 1 }));
      const after = reducer(before, watched("e/2024nyny/m", { qm2: 2 }));
      expect(after.data.e).toEqual({
        "2024casj": { m: { qm1: 1 } },
        "2024nyny": { m: { qm2: 2 } },
      });
      expect(before.data.e).toEqual({ "2024casj": { m: { qm1: 1 } } });
      expect(after.data.e["2024casj"]).toBe(before.data.e["2024casj"]);
    });

    it("stores null when a watched path is deleted", () => {
      let state = reducer(undefined, watched("le/2024casj", { a: 1 }));
      state = reducer(state, watched("le/2024casj", null));
      expect(state.data.le["2024casj"]).toBeNull();
    });
  });
});
