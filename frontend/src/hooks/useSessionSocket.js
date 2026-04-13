import { useEffect, useRef } from 'react';

/**
 * useSessionSocket Hook
 * Manages real-time WebSocket connection to a FOCUS session.
 * @param {string} sessionId - The session ID to watch.
 * @param {Object} handlers - Map of message types to handlers { attendance, phone_alert, session_complete }.
 */
export default function useSessionSocket(sessionId, handlers = {}) {
  const ws = useRef(null);

  useEffect(() => {
    if (!sessionId) return;

    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host === 'localhost:5173' ? 'localhost:8000' : window.location.host;
    const socketUrl = `${protocol}//${host}/ws/session/${sessionId}`;

    console.log(`Connecting to session socket: ${socketUrl}`);
    ws.current = new WebSocket(socketUrl);

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const { type } = data;
        
        if (handlers[type]) {
          handlers[type](data);
        }
      } catch (err) {
        console.error('Failed to parse WS message:', err);
      }
    };

    ws.current.onclose = () => {
      console.log('Session socket closed');
    };

    ws.current.onerror = (err) => {
      console.error('Session socket error:', err);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [sessionId, handlers]);

  return ws.current;
}
