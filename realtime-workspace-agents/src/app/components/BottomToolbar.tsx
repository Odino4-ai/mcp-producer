import React, { useEffect, useCallback } from "react";
import { SessionStatus } from "@/app/types";

interface BottomToolbarProps {
  sessionStatus: SessionStatus;
  onToggleConnection: () => void;
  isPTTActive: boolean;
  setIsPTTActive: (val: boolean) => void;
  isPTTUserSpeaking: boolean;
  handleTalkButtonDown: () => void;
  handleTalkButtonUp: () => void;
  isEventsPaneExpanded: boolean;
  setIsEventsPaneExpanded: (val: boolean) => void;
  isAudioPlaybackEnabled: boolean;
  setIsAudioPlaybackEnabled: (val: boolean) => void;
  codec: string;
  onCodecChange: (newCodec: string) => void;
  isTranscriptVisible: boolean;
  setIsTranscriptVisible: (val: boolean) => void;
  isExpanded?: boolean;
}

function BottomToolbar({
  sessionStatus,
  onToggleConnection,
  isPTTActive,
  setIsPTTActive,
  isPTTUserSpeaking,
  handleTalkButtonDown,
  handleTalkButtonUp,
  isEventsPaneExpanded,
  setIsEventsPaneExpanded,
  isAudioPlaybackEnabled,
  setIsAudioPlaybackEnabled,
  codec,
  onCodecChange,
  isTranscriptVisible,
  setIsTranscriptVisible,
  isExpanded = false,
}: BottomToolbarProps) {
  const isConnected = sessionStatus === "CONNECTED";
  const isConnecting = sessionStatus === "CONNECTING";

  const handleCodecChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newCodec = e.target.value;
    onCodecChange(newCodec);
  };

  function getConnectionButtonLabel() {
    if (isConnected) return "Disconnect";
    if (isConnecting) return "Connecting...";
    return "Connect";
  }

  function getConnectionButtonClasses() {
    const baseClasses =
      "text-base p-2 w-36 rounded-md h-full transition-colors";
    const cursorClass = isConnecting ? "cursor-not-allowed" : "cursor-pointer";

    if (isConnected) {
      // Connected -> label "Disconnect" -> destructive variant
      return `bg-destructive text-destructive-foreground hover:bg-destructive/90 ${cursorClass} ${baseClasses}`;
    }
    // Disconnected or connecting -> label is either "Connect" or "Connecting" -> primary variant
    return `bg-primary text-primary-foreground hover:bg-primary/90 ${cursorClass} ${baseClasses}`;
  }

  // Keyboard event handling for spacebar push-to-talk
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.code === "Space" && !e.repeat && isConnected && isPTTActive) {
        e.preventDefault();
        handleTalkButtonDown();
      }
    },
    [isConnected, isPTTActive, handleTalkButtonDown]
  );

  const handleKeyUp = useCallback(
    (e: KeyboardEvent) => {
      if (e.code === "Space" && isConnected && isPTTActive) {
        e.preventDefault();
        handleTalkButtonUp();
      }
    },
    [isConnected, isPTTActive, handleTalkButtonUp]
  );

  useEffect(() => {
    if (isExpanded) {
      document.addEventListener("keydown", handleKeyDown);
      document.addEventListener("keyup", handleKeyUp);

      return () => {
        document.removeEventListener("keydown", handleKeyDown);
        document.removeEventListener("keyup", handleKeyUp);
      };
    }
  }, [isExpanded, handleKeyDown, handleKeyUp]);

  // Render expanded version when isExpanded is true
  if (isExpanded) {
    return (
      <div className="fixed bottom-12 right-12 z-50">
        <div className="max-w-4xl mx-auto p-6 flex flex-col items-center gap-4">
          {/* Main push-to-talk button */}
          <div className="flex flex-col items-center gap-3">
            <button
              onMouseDown={handleTalkButtonDown}
              onMouseUp={handleTalkButtonUp}
              onTouchStart={handleTalkButtonDown}
              onTouchEnd={handleTalkButtonUp}
              disabled={!isConnected || !isPTTActive}
              className={`w-20 h-20 rounded-full transition-all duration-200 transform ${
                !isConnected || !isPTTActive
                  ? "bg-muted text-muted-foreground cursor-not-allowed scale-95"
                  : isPTTUserSpeaking
                  ? "bg-red-500 text-white shadow-lg scale-105 shadow-red-500/25"
                  : "bg-primary text-primary-foreground hover:bg-primary/90 hover:scale-105 shadow-lg"
              }`}
            >
              <div className="flex flex-col items-center">
                <div className="text-2xl">🎤</div>
              </div>
            </button>

            {/* Instructions */}
            <div className="text-center">
              <div className="text-sm font-medium text-foreground">
                {isPTTUserSpeaking ? "Speaking..." : "Hold to Talk"}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render normal toolbar
  return (
    <div className="p-4 flex flex-row items-center justify-center gap-x-8">
      <button
        onClick={onToggleConnection}
        className={getConnectionButtonClasses()}
        disabled={isConnecting}
      >
        {getConnectionButtonLabel()}
      </button>

      <div className="flex flex-row items-center gap-2">
        <input
          id="push-to-talk"
          type="checkbox"
          checked={isPTTActive}
          onChange={(e) => setIsPTTActive(e.target.checked)}
          disabled={!isConnected}
          className="w-4 h-4"
        />
        <label
          htmlFor="push-to-talk"
          className="flex items-center cursor-pointer text-foreground"
        >
          Push to talk
        </label>
        <button
          onMouseDown={handleTalkButtonDown}
          onMouseUp={handleTalkButtonUp}
          onTouchStart={handleTalkButtonDown}
          onTouchEnd={handleTalkButtonUp}
          disabled={!isPTTActive}
          className={`py-1 px-4 rounded-md transition-colors ${
            !isPTTActive
              ? "bg-muted text-muted-foreground cursor-not-allowed"
              : isPTTUserSpeaking
              ? "bg-accent text-accent-foreground cursor-pointer"
              : "bg-secondary text-secondary-foreground cursor-pointer hover:bg-secondary/80"
          }`}
        >
          Talk
        </button>
      </div>

      <div className="flex flex-row items-center gap-1">
        <input
          id="audio-playback"
          type="checkbox"
          checked={isAudioPlaybackEnabled}
          onChange={(e) => setIsAudioPlaybackEnabled(e.target.checked)}
          disabled={!isConnected}
          className="w-4 h-4"
        />
        <label
          htmlFor="audio-playback"
          className="flex items-center cursor-pointer text-foreground"
        >
          Audio playback
        </label>
      </div>

      <div className="flex flex-row items-center gap-2">
        <input
          id="logs"
          type="checkbox"
          checked={isEventsPaneExpanded}
          onChange={(e) => setIsEventsPaneExpanded(e.target.checked)}
          className="w-4 h-4"
        />
        <label
          htmlFor="logs"
          className="flex items-center cursor-pointer text-foreground"
        >
          Logs
        </label>
      </div>
      <div className="flex flex-row items-center gap-2">
        <input
          id="transcript"
          type="checkbox"
          checked={isTranscriptVisible}
          onChange={(e) => setIsTranscriptVisible(e.target.checked)}
          className="w-4 h-4"
        />
        <label
          htmlFor="transcript"
          className="flex items-center cursor-pointer text-foreground"
        >
          Transcript
        </label>
      </div>

      <div className="flex flex-row items-center gap-2">
        <div className="text-foreground">Codec:</div>
        {/*
          Codec selector – Lets you force the WebRTC track to use 8 kHz 
          PCMU/PCMA so you can preview how the agent will sound 
          (and how ASR/VAD will perform) when accessed via a 
          phone network.  Selecting a codec reloads the page with ?codec=...
          which our App-level logic picks up and applies via a WebRTC monkey
          patch (see codecPatch.ts).
        */}
        <select
          id="codec-select"
          value={codec}
          onChange={handleCodecChange}
          className="border border-input bg-background text-foreground rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-ring cursor-pointer transition-colors"
        >
          <option value="opus">Opus (48 kHz)</option>
          <option value="pcmu">PCMU (8 kHz)</option>
          <option value="pcma">PCMA (8 kHz)</option>
        </select>
      </div>
    </div>
  );
}

export default BottomToolbar;
