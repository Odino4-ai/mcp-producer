// app/api/notion/route.ts
import { NextRequest, NextResponse } from "next/server";
import { NotionAPI } from "notion-client";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const pageId = searchParams.get("notionPageId");
    const defaultPageId = "274a860b701080368183ce1111e68d65";

    // Use provided pageId or fall back to default
    const notionPageId = pageId || defaultPageId;

    const notion = new NotionAPI();
    const data = await notion.getPage(notionPageId);

    return NextResponse.json(data);
  } catch (error: any) {
    console.error(error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
