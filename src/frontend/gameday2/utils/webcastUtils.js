"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
exports.webcastPropType = exports.getWebcastId = void 0;
const prop_types_1 = __importDefault(require("prop-types"));
function getWebcastId(name, num) {
  return `${name}-${num}`;
}
exports.getWebcastId = getWebcastId;
const webcastPropType = prop_types_1.default.shape({
  key: prop_types_1.default.string.isRequired,
  num: prop_types_1.default.number.isRequired,
  id: prop_types_1.default.string.isRequired,
  name: prop_types_1.default.string.isRequired,
  type: prop_types_1.default.string.isRequired,
  channel: prop_types_1.default.string.isRequired,
});
exports.webcastPropType = webcastPropType;
