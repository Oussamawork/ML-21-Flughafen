// Microphone capture via MediaRecorder. Returns a webm/opus Blob on stop.
import { useCallback, useRef, useState } from "react";

export interface Recorder {
  recording: boolean;
  error: string | null;
  start: () => Promise<void>;
  stop: () => Promise<Blob | null>;
}

export function useRecorder(): Recorder {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mr.start();
      mediaRef.current = mr;
      setRecording(true);
    } catch (e) {
      setError(
        "Microphone access denied or unavailable. Use HTTPS or localhost.",
      );
      throw e;
    }
  }, []);

  const stop = useCallback(async (): Promise<Blob | null> => {
    const mr = mediaRef.current;
    if (!mr) return null;
    const blob = await new Promise<Blob>((resolve) => {
      mr.onstop = () =>
        resolve(new Blob(chunksRef.current, { type: "audio/webm" }));
      mr.stop();
    });
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    mediaRef.current = null;
    setRecording(false);
    return blob;
  }, []);

  return { recording, error, start, stop };
}
