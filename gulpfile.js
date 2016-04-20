var gulp = require('gulp');
var source = require('vinyl-source-stream'); // Used to stream bundle for further handling
var browserify = require('browserify');
var watchify = require('watchify');
var reactify = require('reactify');
var gutil = require('gulp-util');
var debug = require('gulp-debug');

var errorHandler = function(err) {
  gutil.log(err);
  this.emit('end');
};

gulp.task('build', function(){
  browserify({
    entries: ['./react/gameday2/gameday2.js'],
    transform: [reactify]
  })
  .bundle()
  .on('error', errorHandler)
  .pipe(source('gameday2.js'))
  .pipe(debug())
  .pipe(gulp.dest('./static/javascript/gameday2/'));
});

gulp.task('browserify', function() {
  var bundler = browserify({
    entries: ['./react/gameday2/gameday2.js'], // Only need initial file, browserify finds the deps
    transform: [reactify], // We want to convert JSX to normal javascript
    debug: true, // Gives us sourcemapping
    cache: {},
    packageCache: {},
    fullPaths: true // Requirement of watchify
  });

  var watcher = watchify(bundler);

  watcher
    .on('update', function() { // When any files update
      var updateStart = Date.now();
      console.log('Updating!');
      watcher.bundle() // Create new bundle that uses the cache for high performance
        .on('error', errorHandler)
        .pipe(source('gameday2.js'))
        .pipe(debug())
        .pipe(gulp.dest('./static/javascript/gameday2/'));
      console.log('Updated!', (Date.now() - updateStart) + 'ms');
    })
    .bundle() // Create the initial bundle when starting the task
    .on('error', errorHandler)
    .pipe(source('gameday2.js'))
    .pipe(debug())
    .pipe(gulp.dest('./static/javascript/gameday2/'));
});

gulp.task('default', ['browserify']);
