const path = require("path");
const webpack = require("webpack");

const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");

const dev = process.env.NODE_ENV !== "production";

module.exports = [
  // Javascript
  {
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
        {
          test: /\.m?js$/,
          resolve: {
            fullySpecified: false,
          },
        },
      ],
    },
    plugins: [
      new webpack.ProvidePlugin({
        process: "process/browser",
      }),
    ],
  },

  // CSS and Less
  {
    entry: [
      "./src/backend/web/static/css/precompiled_css/jquery.fancybox.css",
      "./src/backend/web/static/css/precompiled_css/tablesorter.css",
      "./src/backend/web/static/xcharts/xcharts.min.css",
      "./src/backend/web/static/css/less_css/tba_style.main.less",
    ],
    output: {
      path: path.resolve(__dirname, "src/build/css"),
    },
    plugins: [
      new MiniCssExtractPlugin({
        filename: "tba_combined_style.main.min.css",
      }),
    ],
    module: {
      rules: [
        {
          test: /\.(css|less)$/i,
          use: [
            MiniCssExtractPlugin.loader,
            {
              loader: "css-loader",
              options: {
                url: false,
              },
            },
          ],
        },
        {
          test: /\.less$/i,
          use: [
            {
              loader: "less-loader",
              options: {
                webpackImporter: false,
              },
            },
          ],
        },
      ],
    },
    optimization: {
      minimize: !dev,
      minimizer: [new CssMinimizerPlugin()],
    },
  },
];
