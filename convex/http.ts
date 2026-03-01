import { httpRouter } from "convex/server";
import { postBreach, postLog, getBreaches, postWorkflow, postScanStart, postScanUpdate, postAgentError } from "./httpActions.js";

const http = httpRouter();

http.route({
  path: "/api/breaches",
  method: "GET",
  handler: getBreaches,
});

http.route({
  path: "/api/breach",
  method: "POST",
  handler: postBreach,
});

http.route({
  path: "/api/breach",
  method: "OPTIONS",
  handler: postBreach,
});

http.route({
  path: "/api/log",
  method: "POST",
  handler: postLog,
});

http.route({
  path: "/api/log",
  method: "OPTIONS",
  handler: postLog,
});

http.route({
  path: "/api/workflows",
  method: "POST",
  handler: postWorkflow,
});

http.route({
  path: "/api/workflows",
  method: "OPTIONS",
  handler: postWorkflow,
});

http.route({
  path: "/api/scan/start",
  method: "POST",
  handler: postScanStart,
});

http.route({
  path: "/api/scan/start",
  method: "OPTIONS",
  handler: postScanStart,
});

http.route({
  path: "/api/scan/update",
  method: "POST",
  handler: postScanUpdate,
});

http.route({
  path: "/api/scan/update",
  method: "OPTIONS",
  handler: postScanUpdate,
});

http.route({
  path: "/api/agent-error",
  method: "POST",
  handler: postAgentError,
});

http.route({
  path: "/api/agent-error",
  method: "OPTIONS",
  handler: postAgentError,
});

export default http;
