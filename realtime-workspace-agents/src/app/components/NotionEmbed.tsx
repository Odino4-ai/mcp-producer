"use client";

import React, { useEffect, useState } from "react";
import { NotionRenderer } from "react-notion-x";
import type { ExtendedRecordMap } from "notion-types";

// Import required CSS for react-notion-x
import "react-notion-x/src/styles.css";
import "prismjs/themes/prism-tomorrow.css"; // for code syntax highlighting
import "katex/dist/katex.min.css"; // for math equations
import Link from "next/link";
import { useParams } from "next/navigation";
import { Cross1Icon } from "@radix-ui/react-icons";

function NotionEmbed() {
  // Default Notion page URL if none provided
  const [recordMap, setRecordMap] = useState<ExtendedRecordMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(true);

  // Extract page ID from the URL you provided
  // const defaultPageId = "Development-Projects-274a860b701080368183ce1111e68d65";
  const defaultPageId = "274a860b701080368183ce1111e68d65";
  const params = useParams();
  const pageId = params.pageId as string;
  // www.notion.so/guandjoy/Development-Projects-274a860b701080368183ce1111e68d65?source=copy_link
  const notionPageId = pageId || defaultPageId;

  useEffect(() => {
    const fetchNotionPage = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/notion?notionPageId=${notionPageId}`
        );

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
    const interval = setInterval(fetchNotionPage, 3000); // repeat every 3s
    return () => {
      clearInterval(interval); // cleanup
    };
  }, [notionPageId]);

  return (
    <div
      className={
        "w-1/2 overflow-auto transition-all rounded-xl duration-200 ease-in-out flex-col bg-white"
      }
    >
      <div className="absolute right-2 top-2">
        <Cross1Icon className="w-4 h-4" />
      </div>
      <div className="h-full flex flex-col">
        <div className="flex-1 overflow-auto">
          {loading && !recordMap && (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-500">Loading Notion page...</div>
            </div>
          )}
          {error && (
            <div className="flex items-center justify-center h-full">
              <div className="text-red-500">{error}</div>
            </div>
          )}
          {recordMap && !error && (
            <NotionRenderer
              recordMap={recordMap}
              fullPage={false}
              darkMode={false}
              disableHeader={false}
              className="notion-page"
              components={{
                nextLink: Link,
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default NotionEmbed;
