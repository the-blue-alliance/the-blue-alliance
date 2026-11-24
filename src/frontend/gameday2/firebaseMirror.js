// Keeps a read-only copy of watched Firebase Realtime Database paths in Redux
// state, under `data`, keyed by path segment.

export const FIREBASE_MIRROR_VALUE = "FIREBASE_MIRROR_VALUE";

const initialState = { data: {} };

function setIn(obj, keys, value) {
  if (keys.length === 0) {
    return value;
  }
  const [key, ...rest] = keys;
  const base = obj !== null && typeof obj === "object" ? obj : {};
  return { ...base, [key]: setIn(base[key], rest, value) };
}

export default class FirebaseMirror {
  constructor({ ref }) {
    this.ref = ref;
    this.watching = {};
    this.dispatch = null;
  }

  watch(path) {
    if (this.watching[path]) {
      return;
    }
    this.watching[path] = true;
    this.ref.child(path).on("value", (snapshot) => {
      this.dispatch({
        type: FIREBASE_MIRROR_VALUE,
        path,
        value: snapshot.val(),
      });
    });
  }

  reducer() {
    return (state = initialState, action) => {
      if (action.type !== FIREBASE_MIRROR_VALUE) {
        return state;
      }
      return {
        ...state,
        data: setIn(state.data, action.path.split("/"), action.value),
      };
    };
  }
}
