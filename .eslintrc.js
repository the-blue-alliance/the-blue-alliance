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
    'react/prefer-es6-class': ['warn'],
    // TODO: custom eslint processor to disable this in __test__ directories
    'import/no-extraneous-dependencies': ['error', {
      'devDependencies': true,
    }],
    // TODO: Bootstrap currently requires some elements to be <a> for styling
    // to work properly. This should be fixed in v4; at that time, reenable
    // this rule
    'jsx-a11y/href-no-hash': 'off',
  },
}
