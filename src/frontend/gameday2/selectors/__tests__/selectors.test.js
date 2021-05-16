"use strict";
var __createBinding =
  (this && this.__createBinding) ||
  (Object.create
    ? function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        Object.defineProperty(o, k2, {
          enumerable: true,
          get: function () {
            return m[k];
          },
        });
      }
    : function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        o[k2] = m[k];
      });
var __setModuleDefault =
  (this && this.__setModuleDefault) ||
  (Object.create
    ? function (o, v) {
        Object.defineProperty(o, "default", { enumerable: true, value: v });
      }
    : function (o, v) {
        o["default"] = v;
      });
var __importStar =
  (this && this.__importStar) ||
  function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null)
      for (var k in mod)
        if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k))
          __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
  };
Object.defineProperty(exports, "__esModule", { value: true });
const selectors = __importStar(require("../../selectors"));
describe("getWebcastIds selector", () => {
  const sampleState = {
    webcastsById: {
      a: {},
      b: {},
      c: {},
    },
  };
  it("correctly extracts the ids", () => {
    expect(selectors.getWebcastIds(sampleState)).toEqual(["a", "b", "c"]);
  });
});
describe("getWebcastIdsInDisplayOrder selector", () => {
  const sampleState = {
    webcastsById: {
      a: {
        id: "a",
        sortOrder: 3,
      },
      b: {
        id: "b",
        sortOrder: 1,
      },
      c: {
        id: "c",
        sortOrder: 2,
      },
      d: {
        id: "d",
        name: "ccc",
      },
      e: {
        id: "e",
        name: "aaa",
      },
    },
  };
  it("correctly sorts and returns the ids", () => {
    expect(selectors.getWebcastIdsInDisplayOrder(sampleState)).toEqual([
      "b",
      "c",
      "a",
      "e",
      "d",
    ]);
  });
});
describe("getChats selector", () => {
  it("correctly extracts the chats portion of the state", () => {
    const sampleState = {
      chats: {
        chats: {
          chat: {
            name: "chat",
            channel: "test",
          },
        },
      },
      other: {},
    };
    expect(selectors.getChats(sampleState)).toEqual({
      chats: {
        chat: {
          name: "chat",
          channel: "test",
        },
      },
    });
  });
});
describe("getChatsInDisplayOrder selector", () => {
  it("correctly extrats and sorts the chats", () => {
    const sampleState = {
      chats: {
        chats: {
          chat1: {
            name: "Second in order",
            channel: "chat1",
          },
          chat2: {
            name: "First in order",
            channel: "chat2",
          },
        },
      },
    };
    expect(selectors.getChatsInDisplayOrder(sampleState)).toEqual([
      {
        name: "First in order",
        channel: "chat2",
      },
      {
        name: "Second in order",
        channel: "chat1",
      },
    ]);
  });
});
