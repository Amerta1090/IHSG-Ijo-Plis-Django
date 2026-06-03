export default {
  async fetch(request, env, ctx) {
    const origin = env.PROXY_ORIGIN;

    if (!origin) {
      return new Response(
        "PROXY_ORIGIN not configured. Set it via `wrangler secret put PROXY_ORIGIN` or the Cloudflare dashboard.",
        { status: 500 }
      );
    }

    const url = new URL(request.url);
    const proxyUrl = `${origin}${url.pathname}${url.search}`;

    const headers = new Headers(request.headers);
    headers.set("Host", new URL(origin).host);
    headers.set("X-Forwarded-For", request.headers.get("CF-Connecting-IP") || "");
    headers.set("X-Forwarded-Proto", url.protocol.replace(":", ""));
    headers.set("X-Real-IP", request.headers.get("CF-Connecting-IP") || "");

    const proxyReq = new Request(proxyUrl, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? null : request.body,
    });

    const response = await fetch(proxyReq);
    const responseHeaders = new Headers(response.headers);
    responseHeaders.set("X-Robots-Tag", "noindex");

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  },
};
