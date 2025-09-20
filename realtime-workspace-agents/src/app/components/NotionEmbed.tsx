"use client";

import React, { useEffect, useState } from "react";
import { NotionRenderer } from "react-notion-x";
import type { ExtendedRecordMap } from "notion-types";

// Import required CSS for react-notion-x
import "react-notion-x/src/styles.css";
import "prismjs/themes/prism-tomorrow.css"; // for code syntax highlighting
import "katex/dist/katex.min.css"; // for math equations

export interface NotionEmbedProps {
  isExpanded: boolean;
  pageId?: string;
}

function NotionEmbed({ isExpanded, pageId }: NotionEmbedProps) {
  // Default Notion page URL if none provided
  const [recordMap, setRecordMap] = useState<ExtendedRecordMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Extract page ID from the URL you provided
  // const defaultPageId = "Development-Projects-274a860b701080368183ce1111e68d65";
  const defaultPageId = "274a860b701080368183ce1111e68d65";
  // www.notion.so/guandjoy/Development-Projects-274a860b701080368183ce1111e68d65?source=copy_link
  const notionPageId = pageId || defaultPageId;

  useEffect(() => {
    if (!isExpanded) return;

    const fetchNotionPage = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/notion?pageId=${notionPageId}`);

        if (!response.ok) {
          throw new Error(
            `Failed to fetch: ${response.status} ${response.statusText}`
          );
        }

        const data: ExtendedRecordMap = await response.json();
        setRecordMap(data);
      } catch (err) {
        console.error("Error fetching Notion page:", err);
        setError("Failed to load Notion page");
      } finally {
        setLoading(false);
      }
    };

    fetchNotionPage();
  }, [isExpanded, notionPageId]);

  console.log({ recordMap });

  return (
    <div
      className={
        (isExpanded ? "w-1/2 overflow-auto" : "w-0 overflow-hidden opacity-0") +
        " transition-all rounded-xl duration-200 ease-in-out flex-col bg-white"
      }
    >
      {isExpanded && (
        <div className="h-full flex flex-col">
          <div className="flex items-center justify-between px-6 py-3.5 sticky top-0 z-10 text-base border-b bg-white rounded-t-xl">
            <span className="font-semibold">Development Projects</span>
          </div>
          <div className="flex-1 overflow-auto">
            {loading && (
              <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">Loading Notion page...</div>
              </div>
            )}
            {error && (
              <div className="flex items-center justify-center h-full">
                <div className="text-red-500">{error}</div>
              </div>
            )}
            {recordMap && !loading && !error && (
              <NotionRenderer
                recordMap={recordMap}
                fullPage={false}
                darkMode={false}
                disableHeader={true}
                className="notion-page"
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default NotionEmbed;
