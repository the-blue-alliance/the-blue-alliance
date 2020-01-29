const gulp = require('gulp');
const source = require('vinyl-source-stream');
const browserify = require('browserify');
const watchify = require('watchify');
const log = require('fancy-log');
const debug = require('gulp-debug');
const less = require('gulp-less');
const rename = require('gulp-rename');
const sourcemaps = require('gulp-sourcemaps');
const cleanCSS = require('gulp-clean-css');
const uglify = require('gulp-uglify');
const buffer = require('vinyl-buffer');
const gulpif = require('gulp-if');

const args = require('yargs').argv;

const configs = {
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
  },
  eventwizard: {
    js: {
      src: ['./react/eventwizard/eventwizard.js'],
      outputDir: './static/compiled/javascript',
      outputFile: 'eventwizard.min.js'
    },
    less: {
      src: ['./react/eventwizard/eventwizard.less'],
      outputDir: './static/compiled/css/',
      outputFile: 'eventwizard.min.css',
      watch: ['./react/eventwizard/**/*.less']
    }
  },
  liveevent: {
    js: {
      src: ['./react/liveevent/liveevent.js'],
      outputDir: './static/compiled/javascript',
      outputFile: 'liveevent.min.js'
    }
  },
  zebramotionworks: {
    js: {
      src: ['./react/zebramotionworks/zebramotionworks.js'],
      outputDir: './static/compiled/javascript',
      outputFile: 'zebramotionworks.min.js'
    }
  }
};

const errorHandler = function(err) {
  log.error(err);
  this.emit('end');

  process.exit(1);
};

function compile(watch, config) {
  if (args.production) {
    process.env.NODE_ENV = 'production';
  }
  const bundler = browserify({
    entries: config.js.src,
    debug: true, // Gives us sourcemapping
    cache: {},
    packageCache: {},
  }).transform('babelify');

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
    const watcher = watchify(bundler);
    watcher.on('update', function() {
      rebundle();
    });
  }

  rebundle();
}

function compileLess(config) {
  gulp.src(config.less.src)
    .pipe(sourcemaps.init())
    .pipe(less())
    .pipe(cleanCSS())
    .pipe(sourcemaps.write())
    .pipe(debug())
    .on('error', errorHandler)
    .pipe(rename(config.less.outputFile))
    .pipe(gulp.dest(config.less.outputDir));
}

gulp.task('apidocs-js', (done) => {
  compile(false, configs.apidocs);
  done();
});

gulp.task('apidocs-js-watch', (done) => {
  compile(true, configs.apidocs);
  done();
});

gulp.task('eventwizard-js', (done) => {
  compile(false, configs.eventwizard);
  done();
});

gulp.task('eventwizard-js-watch', (done) => {
  compile(true, configs.eventwizard);
  done();
});

gulp.task('gameday-js', (done) => {
  compile(false, configs.gameday);
  done();
});

gulp.task('gameday-js-watch', (done) => {
  compile(true, configs.gameday);
  done();
});

gulp.task('liveevent-js', (done) => {
  compile(false, configs.liveevent);
  done();
});

gulp.task('liveevent-js-watch', (done) => {
  compile(true, configs.liveevent);
  done();
});


gulp.task('zebramotionworks-js', (done) => {
  compile(false, configs.zebramotionworks);
  done();
});

gulp.task('zebramotionworks-js-watch', (done) => {
  compile(true, configs.zebramotionworks);
  done();
});

gulp.task('apidocs-less', (done) => {
  compileLess(configs.apidocs)
  done();
});

gulp.task('gameday-less', (done) => {
  compileLess(configs.gameday)
  done();
});

gulp.task('eventwizard-less', (done) => {
  compileLess(configs.eventwizard)
  done();
});

gulp.task('gameday-less-watch', (done) => {
  gulp.watch(configs.gameday.less.watch, gulp.series('gameday-less'));
  done();
});

gulp.task('build', gulp.series('gameday-js', 'gameday-less',
                    'apidocs-js', 'apidocs-less',
                    'eventwizard-js', 'eventwizard-less',
                    'liveevent-js', 'zebramotionworks-js'));

gulp.task('watch', gulp.series('gameday-js-watch', 'gameday-less-watch',
                    'apidocs-js-watch',
                    'eventwizard-js-watch',
                    'liveevent-js-watch', 'zebramotionworks-js-watch'));

gulp.task('default', gulp.series('build', 'watch'));
