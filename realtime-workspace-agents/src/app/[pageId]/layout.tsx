"use client";

import React, { Suspense } from "react";
import { TranscriptProvider } from "@/app/contexts/TranscriptContext";
import { EventProvider } from "@/app/contexts/EventContext";
import { WorkspaceProvider } from "@/app/contexts/WorkspaceContext";
import App from "../App";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <TranscriptProvider>
        <EventProvider>
          <WorkspaceProvider>
            <App>{children}</App>
          </WorkspaceProvider>
        </EventProvider>
      </TranscriptProvider>
    </Suspense>
  );
}
