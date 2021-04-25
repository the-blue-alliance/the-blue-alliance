const path = require("path");
const webpack = require("webpack");

const dev = process.env.NODE_ENV !== "production";

module.exports = {
  entry: {
    gameday2: "./src/frontend/gameday2/gameday2.js",
    apidocs: "./src/frontend/apidocs/apidocs.js",
    eventwizard: "./src/frontend/eventwizard/eventwizard.js",
    liveevent: "./src/frontend/liveevent/liveevent.js",
    zebramotionworks: "./src/frontend/zebramotionworks/zebramotionworks.js",
  },
  output: {
    path: path.resolve(__dirname, "./src/build/javascript"),
    filename: "[name].min.js",
    sourceMapFilename: "[name].min.js.map",
  },
  devtool: dev ? "eval-cheap-module-source-map" : "source-map",
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: "babel-loader",
      },
      {
        test: /\.less$/,
        use: [
          { loader: "style-loader" },
          { loader: "css-loader" },
          { loader: "less-loader" },
        ],
      },
    ],
  },
  plugins: [
    new webpack.ProvidePlugin({
      process: "process/browser",
    }),
  ],
};
