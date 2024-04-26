import "./apidocs.less";

import React from "react";
import { createRoot } from "react-dom/client";
import ApiDocsFrame from "./ApiDocsFrame";

const swaggerUrl = document.getElementById("swagger_url").innerHTML;
const container = document.getElementById("content");
const root = createRoot(container);
root.render(<ApiDocsFrame url={swaggerUrl} />);
