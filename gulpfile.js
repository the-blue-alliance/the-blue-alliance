var gulp = require('gulp');
var source = require('vinyl-source-stream');
var browserify = require('browserify');
var watchify = require('watchify');
var gutil = require('gulp-util');
var debug = require('gulp-debug');
var less = require('gulp-less');
var rename = require('gulp-rename');
var sourcemaps = require('gulp-sourcemaps');
var cleanCSS = require('gulp-clean-css');
var babelify = require('babelify');
var uglify = require('gulp-uglify');
var buffer = require('vinyl-buffer');
var gulpif = require('gulp-if');

var args = require('yargs').argv;

var config = {
  gameday: {
    js: {
      src: ['./react/gameday2/gameday2.js'],
      outputDir: './static/compiled/javascript',
      outputFile: 'gameday2.min.js'
    },
    less: {
      src: ['./react/gameday2/gameday2.less'],
      outputDir: './static/compiled/css/',
      outputFile: 'gameday2.min.css',
      watch: ['./react/gameday2/**/*.less']
    }
  },
  apidocs: {
    js: {
      src: ['./react/apidocs/apidocs.js'],
      outputDir: './static/compiled/javascript',
      outputFile: 'apidocs.min.js'
    },
    less: {
      src: ['./react/apidocs/apidocs.less'],
      outputDir: './static/compiled/css/',
      outputFile: 'apidocs.min.css',
      watch: ['./react/apidocs/**/*.less']
    }
  }
};

var errorHandler = function(err) {
  gutil.log(err);
  this.emit('end');
};

function compile(watch, config) {
  if (args.production) {
    process.env.NODE_ENV = 'production';
  }
  var bundler = browserify({
    entries: config.js.src,
    debug: true, // Gives us sourcemapping
    cache: {},
    packageCache: {},
  }).transform('babelify', {
    presets: ['es2015', 'react', 'stage-2']
  });

  function rebundle() {
    bundler.bundle()
      .on('error', errorHandler)
      .pipe(source(config.js.outputFile))
      .pipe(buffer())
      .pipe(sourcemaps.init({loadMaps: true}))
      .pipe(gulpif(args.production, uglify()))
      .on('error', errorHandler)
      .pipe(sourcemaps.write('./'))
      .pipe(debug())
      .pipe(gulp.dest(config.js.outputDir));
  }

  if (watch) {
    var watcher = watchify(bundler);
    watcher.on('update', function() {
      rebundle();
    });
  }

  rebundle();
}

gulp.task('apidocs-js', function() {
  return compile(false, config.apidocs);
});

gulp.task('apidocs-js-watch', function() {
  return compile(true, config.apidocs);
});

gulp.task('gameday-js', function() {
  return compile(false, config.gameday);
});

gulp.task('gameday-js-watch', function() {
  return compile(true, config.gameday);
});

gulp.task('apidocs-less', function() {
  return gulp.src(config.apidocs.less.src)
    .pipe(sourcemaps.init())
    .pipe(less())
    .pipe(cleanCSS())
    .pipe(sourcemaps.write())
    .pipe(debug())
    .on('error', errorHandler)
    .pipe(rename(config.apidocs.less.outputFile))
    .pipe(gulp.dest(config.apidocs.less.outputDir));
});


gulp.task('gameday-less', function() {
  return gulp.src(config.gameday.less.src)
    .pipe(sourcemaps.init())
    .pipe(less())
    .pipe(cleanCSS())
    .pipe(sourcemaps.write())
    .pipe(debug())
    .on('error', errorHandler)
    .pipe(rename(config.gameday.less.outputFile))
    .pipe(gulp.dest(config.gameday.less.outputDir));
});

gulp.task('gameday-less-watch', function() {
  gulp.watch(config.gameday.less.watch, ['gameday-less']);
});

gulp.task('build', ['gameday-js', 'gameday-less', 'apidocs-js', 'apidocs-less']);

gulp.task('watch', ['gameday-js-watch', 'gameday-less-watch', 'apidocs-js-watch']);

gulp.task('default', ['build', 'watch']);
