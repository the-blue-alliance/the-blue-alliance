module.exports = {
    "extends": "airbnb",
    "plugins": [
        "react",
    ],
    "env": {
      "jest": true,
      "jasmine": true,
    },
    "rules": {
      "semi": "off",
      "max-len": ['warn', 100, 2, {
        // ignore long it(...) lines in jasmine unit tests
        "ignorePattern": ".*it\\(.*\\).*"
      }],
    }
};
