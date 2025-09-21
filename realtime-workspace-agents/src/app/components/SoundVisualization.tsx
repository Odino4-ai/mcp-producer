"use client";

import React, { useEffect, useRef } from "react";

interface SoundVisualizationProps {
  audioElement: HTMLAudioElement | null;
  isVisible: boolean;
  className?: string;
}

const SoundVisualization: React.FC<SoundVisualizationProps> = ({
  audioElement,
  isVisible,
  className = "",
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  // Initialize audio analysis
  useEffect(() => {
    if (!audioElement || !isVisible) {
      cleanup();
      return;
    }

    const initializeAudioAnalysis = () => {
      try {
        // Check if audio element has a stream
        const stream = audioElement.srcObject as MediaStream;
        if (!stream) {
          console.log("No audio stream available yet");
          return;
        }

        // Create audio context if it doesn't exist
        if (!audioContextRef.current) {
          audioContextRef.current = new AudioContext();
        }

        const audioContext = audioContextRef.current;

        // Resume audio context if suspended
        if (audioContext.state === "suspended") {
          audioContext.resume();
        }

        // Create analyser node
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.8;

        // Create source from stream
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);

        // Create data array for frequency data
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        analyserRef.current = analyser;
        dataArrayRef.current = dataArray;
        sourceRef.current = source;

        startVisualization();
      } catch (error) {
        console.error("Error initializing audio analysis:", error);
      }
    };

    // Try to initialize immediately
    initializeAudioAnalysis();

    // Also listen for when the audio element gets a stream
    const handleLoadedMetadata = () => {
      initializeAudioAnalysis();
    };

    audioElement.addEventListener("loadedmetadata", handleLoadedMetadata);

    return () => {
      audioElement.removeEventListener("loadedmetadata", handleLoadedMetadata);
      cleanup();
    };
  }, [audioElement, isVisible]);

  const cleanup = () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    if (sourceRef.current) {
      try {
        sourceRef.current.disconnect();
      } catch (e) {
        // Ignore disconnect errors
      }
      sourceRef.current = null;
    }

    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    dataArrayRef.current = null;
  };

  const startVisualization = () => {
    if (!canvasRef.current || !analyserRef.current || !dataArrayRef.current) {
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const analyser = analyserRef.current;
    const dataArray = dataArrayRef.current;

    const draw = () => {
      if (!isVisible || !analyser || !dataArray) {
        return;
      }

      animationRef.current = requestAnimationFrame(draw);

      // Get frequency data
      analyser.getByteFrequencyData(dataArray);

      // Clear canvas with transparent background
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Calculate average volume for overall amplitude
      const average =
        dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
      const normalizedAverage = average / 255;

      // Only draw if there's significant audio activity
      if (normalizedAverage > 0.02) {
        // Draw simplified frequency bars (fewer bars for compact size)
        const numBars = 40; // Reduced number of bars for compact display
        const barWidth = canvas.width / numBars;

        for (let i = 0; i < numBars; i++) {
          // Sample frequency data at intervals
          const dataIndex = Math.floor((i / numBars) * dataArray.length);
          const barHeight = (dataArray[dataIndex] / 255) * canvas.height * 0.8;

          if (barHeight > 2) {
            // Only draw bars with meaningful height
            // Simple gradient from bottom to top
            const gradient = ctx.createLinearGradient(
              0,
              canvas.height,
              0,
              canvas.height - barHeight
            );
            gradient.addColorStop(0, "rgba(59, 130, 246, 0.8)"); // blue with transparency
            gradient.addColorStop(1, "rgba(6, 182, 212, 0.9)"); // cyan with transparency

            ctx.fillStyle = gradient;
            ctx.fillRect(
              i * barWidth,
              canvas.height - barHeight,
              barWidth - 1,
              barHeight
            );
          }
        }
      }
    };

    draw();
  };

  // Handle canvas resize
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;

      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
      }
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    return () => {
      window.removeEventListener("resize", resizeCanvas);
    };
  }, []);

  if (!isVisible) {
    return null;
  }

  return (
    <div className={`fixed bottom-12 left-8 z-50 ${className}`}>
      <canvas
        ref={canvasRef}
        className="rounded-lg"
        style={{ width: "400px", height: "200px" }}
      />
    </div>
  );
};

export default SoundVisualization;
