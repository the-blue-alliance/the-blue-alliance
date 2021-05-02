const path = require("path");
const webpack = require("webpack");

const dev = process.env.NODE_ENV !== "production";

module.exports = {
    entry: {
        gameday2: "./react/gameday2/gameday2.js",
        apidocs: "./react/apidocs/apidocs.js",
        eventwizard: "./react/eventwizard/eventwizard.js",
        liveevent: "./react/liveevent/liveevent.js",
        zebramotionworks: "./react/zebramotionworks/zebramotionworks.js",
    },
    output: {
        path: path.resolve(__dirname, "./static/compiled/javascript"),
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
