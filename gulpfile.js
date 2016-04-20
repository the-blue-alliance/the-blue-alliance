var gulp = require('gulp');
var source = require('vinyl-source-stream'); // Used to stream bundle for further handling
var browserify = require('browserify');
var watchify = require('watchify');
var reactify = require('reactify');
var gutil = require('gulp-util');
var debug = require('gulp-debug');
var babelify = require('babelify');

var errorHandler = function(err) {
  gutil.log(err);
  this.emit('end');
};

function compile(watch) {
  var bundler = browserify({
    entries: ['./react/gameday2/gameday2.js'], // Only need initial file, browserify finds the deps
    debug: true, // Gives us sourcemapping
    cache: {},
    packageCache: {},
    fullPaths: true // Requirement of watchify
  }).transform('babelify', {
    presets: ['es2015', 'react']
  });

  var watcher = watchify(bundler);

  function rebundle() {
    bundler.bundle()
      .on('error', errorHandler)
      .pipe(source('gameday2.js'))
      .pipe(debug())
      .pipe(gulp.dest('./static/javascript/gameday2/'));
  }

  if (watch) {
    watcher.on('update', function() {
      rebundle();
    });
  }

  rebundle();
}

function watch() {
  return compile(true);
}

gulp.task('build', function() {
  return compile();
});

gulp.task('watch', function() {
  return watch();
});

gulp.task('default', ['watch']);
