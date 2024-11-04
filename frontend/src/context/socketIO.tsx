import React from "react";
import { Data } from "ws";
import { io, Socket } from "socket.io-client";
import EventLogger from "#/utils/event-logger";

interface SocketIOClientOptions {
  token: string | null;
  onOpen?: () => void;
  onMessage?: (data: Data) => void;
  onError?: (event: Event) => void;
  onClose?: () => void;
}

interface SocketIOContextType {
  send: (data: any) => void;
  start: (options?: SocketIOClientOptions) => void;
  stop: () => void;
  setRuntimeIsInitialized: () => void;
  runtimeActive: boolean;
  isConnected: boolean;
  events: Record<string, unknown>[];
}

const SocketIOContext = React.createContext<SocketIOContextType | undefined>(
  undefined,
);

interface SocketProviderProps {
  children: React.ReactNode;
}

function SocketIOProvider({ children }: SocketProviderProps) {
  const sioRef = React.useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = React.useState(false);
  const [runtimeActive, setRuntimeActive] = React.useState(false);
  const [events, setEvents] = React.useState<Record<string, unknown>[]>([]);

  const setRuntimeIsInitialized = () => {
    setRuntimeActive(true);
  };

  const start = React.useCallback((options?: SocketIOClientOptions): void => {
    if (sioRef.current) {
      EventLogger.warning(
        "SocketIO connection is already established, but a new one is starting anyways.",
      );
    }

    const baseUrl =
      import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host;
    // const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const sessionToken = options?.token || "NO_JWT"; // not allowed to be empty or duplicated
    const ghToken = localStorage.getItem("ghToken") || "NO_GITHUB";

    const sio = io(
      `${window.location.protocol}//${baseUrl}${options?.token ? `?token=${options.token}` : ""}`,
      {
        transports: ['websocket']
      });

    sio.on("connect", () => {
      setIsConnected(true);
      options?.onOpen?.();
    });

    sio.on("oh_event", (message) => {
      if (EventLogger.isDevMode) {
        console.warn(message);
      }
      setEvents((prevEvents) => [...prevEvents, message]);
      options?.onMessage?.(message);
    });

    const onError = (err: any) => {
      EventLogger.event(err, "SOCKETIO ERROR");
      options?.onError?.(err);
    }

    sio.on('connect_error', onError)
    sio.on('connect_failed', onError)
    sio.on('disconnect', (ev: any) => {
      EventLogger.event(ev, "SOCKETIO CLOSE");

      setIsConnected(false);
      setRuntimeActive(false);
      sioRef.current = null;
      options?.onClose?.();
    });

    sioRef.current = sio;
  }, []);

  const stop = React.useCallback((): void => {
    if (sioRef.current) {
      sioRef.current.close();
      sioRef.current = null;
    }
  }, []);

  const send = React.useCallback(
    (data: any) => {
      if (!sioRef.current) {
        EventLogger.error("SocketIO is not connected.");
        return;
      }
      setEvents((prevEvents) => [...prevEvents, data]);
      sioRef.current.emit("oh_action", data);
    },
    [],
  );

  const value = React.useMemo(
    () => ({
      send,
      start,
      stop,
      setRuntimeIsInitialized,
      runtimeActive,
      isConnected,
      events,
    }),
    [
      send,
      start,
      stop,
      setRuntimeIsInitialized,
      runtimeActive,
      isConnected,
      events,
    ],
  );

  return (
    <SocketIOContext.Provider value={value}>{children}</SocketIOContext.Provider>
  );
}

function useSocketIO() {
  const context = React.useContext(SocketIOContext);
  if (context === undefined) {
    throw new Error("useSocketIO must be used within a SocketIOProvider");
  }
  return context;
}

export { SocketIOProvider, useSocketIO };
