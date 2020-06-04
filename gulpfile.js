const gulp = require("gulp");
const source = require("vinyl-source-stream");
const browserify = require("browserify");
const watchify = require("watchify");
const log = require("fancy-log");
const debug = require("gulp-debug");
const less = require("gulp-less");
const rename = require("gulp-rename");
const sourcemaps = require("gulp-sourcemaps");
const cleanCSS = require("gulp-clean-css");
const uglify = require("gulp-uglify");
const buffer = require("vinyl-buffer");
const gulpif = require("gulp-if");

const args = require("yargs").argv;

const configs = {
  gameday: {
    js: {
      src: ["./src/frontend/gameday2/gameday2.js"],
      outputDir: "./src/build/javascript",
      outputFile: "gameday2.min.js",
    },
    less: {
      src: ["./src/frontend/gameday2/gameday2.less"],
      outputDir: "./src/build/css/",
      outputFile: "gameday2.min.css",
      watch: ["./src/frontend/gameday2/**/*.less"],
    },
  },
  apidocs: {
    js: {
      src: ["./src/frontend/apidocs/apidocs.js"],
      outputDir: "./src/build/javascript",
      outputFile: "apidocs.min.js",
    },
    less: {
      src: ["./src/frontend/apidocs/apidocs.less"],
      outputDir: "./src/build/css/",
      outputFile: "apidocs.min.css",
      watch: ["./src/frontend/apidocs/**/*.less"],
    },
  },
  eventwizard: {
    js: {
      src: ["./src/frontend/eventwizard/eventwizard.js"],
      outputDir: "./src/build/javascript",
      outputFile: "eventwizard.min.js",
    },
    less: {
      src: ["./src/frontend/eventwizard/eventwizard.less"],
      outputDir: "./src/build/css/",
      outputFile: "eventwizard.min.css",
      watch: ["./src/frontend/eventwizard/**/*.less"],
    },
  },
  liveevent: {
    js: {
      src: ["./src/frontend/liveevent/liveevent.js"],
      outputDir: "./src/build/javascript",
      outputFile: "liveevent.min.js",
    },
  },
  zebramotionworks: {
    js: {
      src: ["./src/frontend/zebramotionworks/zebramotionworks.js"],
      outputDir: "./src/build/javascript",
      outputFile: "zebramotionworks.min.js",
    },
  },
};

const errorHandler = function (err) {
  log.error(err);
  this.emit("end");

  process.exit(1);
};

function compile(watch, config) {
  if (args.production) {
    process.env.NODE_ENV = "production";
  }
  const bundler = browserify({
    entries: config.js.src,
    debug: true, // Gives us sourcemapping
    cache: {},
    packageCache: {},
  }).transform("babelify");

  function rebundle() {
    bundler
      .bundle()
      .on("error", errorHandler)
      .pipe(source(config.js.outputFile))
      .pipe(buffer())
      .pipe(sourcemaps.init({ loadMaps: true }))
      .pipe(gulpif(args.production, uglify()))
      .on("error", errorHandler)
      .pipe(sourcemaps.write("./"))
      .pipe(debug())
      .pipe(gulp.dest(config.js.outputDir));
  }

  if (watch) {
    const watcher = watchify(bundler);
    watcher.on("update", function () {
      rebundle();
    });
  }

  rebundle();
}

function compileLess(config) {
  gulp
    .src(config.less.src)
    .pipe(sourcemaps.init())
    .pipe(less())
    .pipe(cleanCSS())
    .pipe(sourcemaps.write())
    .pipe(debug())
    .on("error", errorHandler)
    .pipe(rename(config.less.outputFile))
    .pipe(gulp.dest(config.less.outputDir));
}

gulp.task("apidocs-js", (done) => {
  compile(false, configs.apidocs);
  done();
});

gulp.task("apidocs-js-watch", (done) => {
  compile(true, configs.apidocs);
  done();
});

gulp.task("eventwizard-js", (done) => {
  compile(false, configs.eventwizard);
  done();
});

gulp.task("eventwizard-js-watch", (done) => {
  compile(true, configs.eventwizard);
  done();
});

gulp.task("gameday-js", (done) => {
  compile(false, configs.gameday);
  done();
});

gulp.task("gameday-js-watch", (done) => {
  compile(true, configs.gameday);
  done();
});

gulp.task("liveevent-js", (done) => {
  compile(false, configs.liveevent);
  done();
});

gulp.task("liveevent-js-watch", (done) => {
  compile(true, configs.liveevent);
  done();
});

gulp.task("zebramotionworks-js", (done) => {
  compile(false, configs.zebramotionworks);
  done();
});

gulp.task("zebramotionworks-js-watch", (done) => {
  compile(true, configs.zebramotionworks);
  done();
});

gulp.task("apidocs-less", (done) => {
  compileLess(configs.apidocs);
  done();
});

gulp.task("gameday-less", (done) => {
  compileLess(configs.gameday);
  done();
});

gulp.task("eventwizard-less", (done) => {
  compileLess(configs.eventwizard);
  done();
});

gulp.task("gameday-less-watch", (done) => {
  gulp.watch(configs.gameday.less.watch, gulp.series("gameday-less"));
  done();
});

gulp.task(
  "build",
  gulp.series(
    "gameday-js",
    "gameday-less",
    "apidocs-js",
    "apidocs-less",
    "eventwizard-js",
    "eventwizard-less",
    "liveevent-js",
    "zebramotionworks-js"
  )
);

gulp.task(
  "watch",
  gulp.series(
    "gameday-js-watch",
    "gameday-less-watch",
    "apidocs-js-watch",
    "eventwizard-js-watch",
    "liveevent-js-watch",
    "zebramotionworks-js-watch"
  )
);

gulp.task("default", gulp.series("build", "watch"));
