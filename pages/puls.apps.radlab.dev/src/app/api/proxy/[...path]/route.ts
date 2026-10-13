import { NextRequest, NextResponse } from "next/server";

import { getAppConfig } from "@/config/app-config";

/**
 * Server-side proxy for the radlab backend.
 *
 * Why a proxy:
 *  - The backend is an intranet service without CORS headers, so browsers
 *    cannot call it directly.
 *  - It keeps the backend host in server-side env config only (never in the
 *    client bundle), mirroring how the Streamlit UI resolves host/endpoints
 *    from ui-configuration.json on the server.
 *
 * The raw backend response (status + JSON body) is returned unchanged so the
 * client can apply the same "{status, body}" unwrapping used by the Streamlit
 * UI (BasePublicApiInterface.return_response).
 */

const ROUTES: Record<
  string,
  { endpointKey: "newsCategoriesWithPages" | "searchNews" | "generateArticle" }
> = {
  news_categories_with_pages: { endpointKey: "newsCategoriesWithPages" },
  search_news: { endpointKey: "searchNews" },
  generate_article: { endpointKey: "generateArticle" },
};

type RouteContext = { params: Promise<{ path: string[] }> };

function targetFor(pathName: string): string | null {
  const route = ROUTES[pathName];
  if (!route) return null;
  const { host, endpoints } = getAppConfig();
  return `${host}/${endpoints[route.endpointKey]}`;
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const target = targetFor(path[0]);
  if (!target) {
    return NextResponse.json({ error: "Unknown proxy route" }, { status: 404 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(target, { method: "GET", cache: "no-store" });
  } catch (err) {
    return NextResponse.json(
      {
        status: false,
        body: null,
        error: `Upstream request failed: ${
          err instanceof Error ? err.message : String(err)
        }`,
      },
      { status: 502 }
    );
  }

  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "content-type":
        upstream.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store",
    },
  });
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const target = targetFor(path[0]);
  if (!target) {
    return NextResponse.json({ error: "Unknown proxy route" }, { status: 404 });
  }

  const form = await request.text();

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: form,
      cache: "no-store",
    });
  } catch (err) {
    return NextResponse.json(
      {
        status: false,
        body: null,
        error: `Upstream request failed: ${
          err instanceof Error ? err.message : String(err)
        }`,
      },
      { status: 502 }
    );
  }

  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "content-type":
        upstream.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store",
    },
  });
}
