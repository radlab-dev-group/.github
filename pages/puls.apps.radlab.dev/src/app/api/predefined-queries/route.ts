import { NextResponse } from "next/server";

import { drawPredefinedQueries } from "@/lib/predefined-queries";

/**
 * Draws the predefined search phrases (kreator-pytania.txt) server-side so a
 * fresh random subset is served on every page entry / refresh.
 */
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET() {
  try {
    const queries = await drawPredefinedQueries();
    return NextResponse.json(
      { queries },
      { headers: { "cache-control": "no-store" } }
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { queries: [], error: message },
      { status: 500, headers: { "cache-control": "no-store" } }
    );
  }
}
