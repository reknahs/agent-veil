import { httpRouter } from "convex/server";
import { postBreach, postLog, getBreaches } from "./httpActions.js";

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

export default http;
