import { createRoot } from "react-dom/client";
import "./apidocs.less";

import React from "react";
import ReactDOM from "react-dom";
import ApiDocsFrame from "./ApiDocsFrame";

const swaggerUrl = document.getElementById("swagger_url").innerHTML;
const root = createRoot(document.getElementById("content"));
root.render(<ApiDocsFrame url={swaggerUrl} />);
