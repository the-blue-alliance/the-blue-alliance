module.exports = {
  'extends': 'airbnb',
  'plugins': [
    'react',
  ],
  'env': {
    'jest': true,
    'jasmine': true,
    'browser': true,
    'jquery': true,
  },
  'rules': {
    'semi': ['error', 'never'],
    'max-len': ['warn', 100, 2, {
        // ignore long it(...) lines in jasmine unit tests
      'ignorePattern': '.*it\\(.*\\).*',
    }],
    'react/jsx-filename-extension': 'off',
    'react/prefer-es6-class': ['warn']
  },
}
