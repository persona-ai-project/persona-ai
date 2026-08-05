"use client";

import { motion } from "framer-motion";
import { Mic, Square } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface VoiceButtonProps {
  onTranscription?: (text: string) => void;
}

export function VoiceButton({ onTranscription }: VoiceButtonProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((track) => track.stop());

        setIsProcessing(true);
        try {
          const formData = new FormData();
          formData.append("file", audioBlob, "recording.webm");

          const response = await fetch(`${API_URL}/voice/transcribe`, {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${localStorage.getItem("access_token") || ""}`,
            },
            body: formData,
          });

          if (response.ok) {
            const data = await response.json();
            if (data.text && onTranscription) {
              onTranscription(data.text);
            }
          }
        } catch (error) {
          console.error("Transcription failed:", error);
        } finally {
          setIsProcessing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Failed to start recording:", error);
    }
  }, [onTranscription]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);

  const handleClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <Button
      type="button"
      variant="outline"
      size="icon"
      aria-label={isRecording ? "Stop recording" : "Start recording"}
      aria-pressed={isRecording}
      onClick={handleClick}
      disabled={isProcessing}
      className={cn(
        "relative shrink-0 transition-colors",
        isRecording &&
          "border-destructive bg-destructive/20 text-destructive hover:bg-destructive/30 hover:text-destructive",
        isProcessing &&
          "border-yellow-500 bg-yellow-500/20 text-yellow-500"
      )}
    >
      {(isRecording || isProcessing) && (
        <motion.span
          className="absolute inset-0 rounded-lg bg-destructive/30"
          animate={{ scale: [1, 1.15, 1], opacity: [0.6, 0.2, 0.6] }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
        />
      )}
      {isRecording ? (
        <Square className={cn("relative z-10 size-4 text-destructive")} />
      ) : (
        <Mic className={cn("relative z-10 size-4", isProcessing && "text-yellow-500")} />
      )}
    </Button>
  );
}
