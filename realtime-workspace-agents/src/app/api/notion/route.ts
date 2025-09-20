// app/api/notion/route.ts
import { NextResponse } from "next/server";
import { NotionAPI } from "notion-client";

export async function GET() {
  try {
    const defaultPageId = "274a860b701080368183ce1111e68d65";
    const notion = new NotionAPI();
    const data = await notion.getPage(defaultPageId);

    return NextResponse.json(data);
  } catch (error: any) {
    console.error(error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
