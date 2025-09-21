"use client";

import React, { useEffect, useState, useRef } from "react";
import { NotionRenderer } from "react-notion-x";
import type { ExtendedRecordMap } from "notion-types";

// Import required CSS for react-notion-x
import "react-notion-x/src/styles.css";
import "prismjs/themes/prism-tomorrow.css"; // for code syntax highlighting
import "katex/dist/katex.min.css"; // for math equations
import Link from "next/link";
import { useParams } from "next/navigation";
import { Cross1Icon, EnterFullScreenIcon } from "@radix-ui/react-icons";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function NotionEmbed({
  isExpanded,
  setIsExpanded,
}: {
  isExpanded: boolean;
  setIsExpanded: (val: boolean) => void;
}) {
  // Default Notion page URL if none provided
  const [recordMap, setRecordMap] = useState<ExtendedRecordMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Refs for smart scroll
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const isUserScrollingRef = useRef(false);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastContentRef = useRef<string>("");

  // Extract page ID from the URL you provided
  // const defaultPageId = "Development-Projects-274a860b701080368183ce1111e68d65";
  const defaultPageId = "274a860b701080368183ce1111e68d65";
  const params = useParams();
  const pageId = params.pageId as string;
  // www.notion.so/guandjoy/Development-Projects-274a860b701080368183ce1111e68d65?source=copy_link
  const notionPageId = pageId || defaultPageId;

  // Force scroll to bottom (always scrolls, regardless of user interaction)
  const forceScrollToBottom = () => {
    if (scrollContainerRef.current) {
      const { scrollHeight, clientHeight } = scrollContainerRef.current;
      scrollContainerRef.current.scrollTop = scrollHeight - clientHeight;
    }
  };

  // Smart scroll to bottom (respects user interaction)
  const scrollToBottom = () => {
    if (scrollContainerRef.current && !isUserScrollingRef.current) {
      forceScrollToBottom();
    }
  };

  // Handle user scroll
  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } =
        scrollContainerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 10; // Increased tolerance

      if (!isAtBottom) {
        isUserScrollingRef.current = true;
        if (scrollTimeoutRef.current) {
          clearTimeout(scrollTimeoutRef.current);
        }
        // Reset auto-scroll after 3 seconds of no user interaction
        scrollTimeoutRef.current = setTimeout(() => {
          isUserScrollingRef.current = false;
        }, 3000);
      } else {
        // User is at bottom, enable auto-scroll
        isUserScrollingRef.current = false;
        if (scrollTimeoutRef.current) {
          clearTimeout(scrollTimeoutRef.current);
        }
      }
    }
  };

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
        const newContentHash = JSON.stringify(data);

        // Check if content has actually changed
        if (newContentHash !== lastContentRef.current) {
          setRecordMap(data);
          lastContentRef.current = newContentHash;

          // Always scroll to bottom when new content appears
          setTimeout(forceScrollToBottom, 150);
        } else if (!recordMap) {
          // First load
          setRecordMap(data);
          lastContentRef.current = newContentHash;
          setTimeout(forceScrollToBottom, 150);
        }
      } catch (err) {
        console.error("Error fetching Notion page:", err);
        setError("Failed to load Notion page");
      } finally {
        setLoading(false);
      }
    };

    fetchNotionPage();
    const interval = setInterval(fetchNotionPage, 3000); // repeat every 3s

    // Add scroll listener
    const scrollContainer = scrollContainerRef.current;
    if (scrollContainer) {
      scrollContainer.addEventListener("scroll", handleScroll);
    }

    return () => {
      clearInterval(interval); // cleanup
      if (scrollContainer) {
        scrollContainer.removeEventListener("scroll", handleScroll);
      }
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [notionPageId]);

  // Additional effect to ensure scrolling when recordMap changes
  useEffect(() => {
    if (recordMap) {
      // Use a longer delay to ensure DOM has updated
      const timer = setTimeout(() => {
        forceScrollToBottom();
      }, 200);

      return () => clearTimeout(timer);
    }
  }, [recordMap]);

  return (
    <div
      className={cn(
        isExpanded
          ? "fixed inset-0 top-[68px] z-50"
          : "w-1/2 overflow-auto transition-all rounded-xl duration-200 ease-in-out flex-col bg-white",
        "bg-background ring-1 ring-border z-10"
      )}
    >
      {isExpanded ? (
        <Button
          size="icon"
          variant="secondary"
          onClick={() => setIsExpanded(false)}
          className="absolute z-20 right-4 top-2"
        >
          <Cross1Icon />
        </Button>
      ) : (
        <Button
          size="icon"
          variant="secondary"
          onClick={() => setIsExpanded(true)}
          className="absolute z-20 right-4 top-2"
        >
          <EnterFullScreenIcon />
        </Button>
      )}
      <div className="h-full flex flex-col">
        <div className="flex-1 overflow-auto" ref={scrollContainerRef}>
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
              darkMode={true}
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
