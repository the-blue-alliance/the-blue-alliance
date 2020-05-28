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
    'react/forbid-prop-types': ['warn', {
      'forbid': ['array'],
    }],
    'react/prefer-es6-class': ['warn'],
    'import/no-extraneous-dependencies': ['error', {
      'devDependencies': true,
    }],
    'no-plusplus': ['error', {
      'allowForLoopAfterthoughts': true,
    }],
    'arrow-parens': ['error', 'always'],
    'comma-dangle': ['error', {
      'functions': 'never',
      'arrays': 'always-multiline',
      'objects': 'always-multiline',
      'imports': 'always-multiline',
      'exports': 'always-multiline',
    }],
  },
}
