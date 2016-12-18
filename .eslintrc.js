module.exports = {
  'parser': 'babel-eslint',
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
    'max-len': 'off',
    'react/jsx-filename-extension': 'off',
    'react/prefer-es6-class': ['warn'],
    'import/no-extraneous-dependencies': ['error', {
      'devDependencies': true,
    }],
    'no-plusplus': ['error', {
      'allowForLoopAfterthoughts': true
    }],
  },
}
