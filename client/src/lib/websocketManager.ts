/**
 * WebSocket Singleton Manager
 *
 * Ensures only one WebSocket connection exists globally, even with React StrictMode.
 * Supports multiple subscribers that can listen to the same connection.
 *
 * Phase 3 Optimization: Supports MessagePack binary decoding with JSON fallback
 */

import { decode } from '@msgpack/msgpack';

type MessageHandler = (data: any) => void;
type ConnectionHandler = () => void;
type ErrorHandler = (error: Event) => void;

interface Subscriber {
  id: string;
  onMessage: MessageHandler;
  onConnect?: ConnectionHandler;
  onDisconnect?: ConnectionHandler;
  onError?: ErrorHandler;
}

class WebSocketManager {
  private static instance: WebSocketManager | null = null;
  private ws: WebSocket | null = null;
  private url: string | null = null;
  private subscribers: Map<string, Subscriber> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private reconnectTimer: number | null = null;
  private disconnectTimer: number | null = null; // Delay disconnect for StrictMode
  private isIntentionallyClosed = false;

  private constructor() {
    // Singleton - private constructor
  }

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  /**
   * Connect to WebSocket server (creates connection if doesn't exist)
   */
  connect(url: string): void {
    // If already connected or connecting to this URL, do nothing
    if (this.ws && this.url === url) {
      const state = this.ws.readyState;
      if (state === WebSocket.OPEN || state === WebSocket.CONNECTING) {
        console.log('[WebSocketManager] Already connected/connecting to', url);
        return;
      }
    }

    // If connecting to different URL, close existing connection
    if (this.ws && this.url !== url) {
      console.log('[WebSocketManager] Switching to new URL:', url);
      this.disconnect();
    }

    // Cancel any pending disconnect (handles StrictMode double-render)
    if (this.disconnectTimer) {
      console.log('[WebSocketManager] Cancelling pending disconnect');
      clearTimeout(this.disconnectTimer);
      this.disconnectTimer = null;
    }

    this.url = url;
    this.isIntentionallyClosed = false;
    this.createConnection();
  }

  private createConnection(): void {
    if (!this.url) return;

    console.log('[WebSocketManager] Creating connection to', this.url);

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('[WebSocketManager] Connected to', this.url);
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;

      // Notify all subscribers
      this.subscribers.forEach(sub => {
        sub.onConnect?.();
      });
    };

    this.ws.onmessage = (event) => {
      let data: any;

      // Phase 3 Optimization: Decode MessagePack binary or parse JSON
      if (event.data instanceof ArrayBuffer || event.data instanceof Blob) {
        // Binary message - decode MessagePack
        try {
          if (event.data instanceof Blob) {
            // Convert Blob to ArrayBuffer
            event.data.arrayBuffer().then(buffer => {
              data = decode(new Uint8Array(buffer));
              this.processMessage(data);
            });
            return;
          } else {
            // Already ArrayBuffer
            data = decode(new Uint8Array(event.data));
          }
        } catch (error) {
          console.error('[WebSocketManager] Failed to decode MessagePack:', error);
          return;
        }
      } else {
        // Text message - parse JSON (fallback for backward compatibility)
        try {
          data = JSON.parse(event.data);
        } catch (error) {
          console.error('[WebSocketManager] Failed to parse JSON:', error);
          return;
        }
      }

      this.processMessage(data);
    };

    this.ws.onclose = () => {
      console.log('[WebSocketManager] Disconnected from', this.url);

      // Notify all subscribers
      this.subscribers.forEach(sub => {
        sub.onDisconnect?.();
      });

      // Attempt reconnection unless intentionally closed
      if (!this.isIntentionallyClosed && this.subscribers.size > 0) {
        this.attemptReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WebSocketManager] Error:', error);

      // Notify all subscribers
      this.subscribers.forEach(sub => {
        sub.onError?.(error);
      });
    };
  }

  private processMessage(data: any): void {
    // Handle ping messages globally
    if (data.type === 'ping') {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'pong' }));
      }
      return;
    }

    // Broadcast to all subscribers
    this.subscribers.forEach(sub => {
      sub.onMessage(data);
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocketManager] Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff

    console.log(
      `[WebSocketManager] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    this.reconnectTimer = window.setTimeout(() => {
      if (this.url && !this.isIntentionallyClosed) {
        this.createConnection();
      }
    }, delay);
  }

  /**
   * Subscribe to WebSocket events
   * Returns unsubscribe function
   */
  subscribe(
    onMessage: MessageHandler,
    onConnect?: ConnectionHandler,
    onDisconnect?: ConnectionHandler,
    onError?: ErrorHandler
  ): () => void {
    const id = Math.random().toString(36).substring(7);

    this.subscribers.set(id, {
      id,
      onMessage,
      onConnect,
      onDisconnect,
      onError,
    });

    console.log(`[WebSocketManager] Subscriber ${id} added (total: ${this.subscribers.size})`);

    // Cancel any pending disconnect (new subscriber joined)
    if (this.disconnectTimer) {
      console.log('[WebSocketManager] Cancelling pending disconnect - new subscriber joined');
      clearTimeout(this.disconnectTimer);
      this.disconnectTimer = null;
    }

    // If already connected, immediately call onConnect
    if (this.ws?.readyState === WebSocket.OPEN) {
      onConnect?.();
    }

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(id);
      console.log(`[WebSocketManager] Subscriber ${id} removed (total: ${this.subscribers.size})`);

      // If no more subscribers, schedule disconnect after a delay
      // This handles React StrictMode's double-mount pattern
      if (this.subscribers.size === 0) {
        console.log('[WebSocketManager] No more subscribers, scheduling disconnect in 100ms');
        this.disconnectTimer = window.setTimeout(() => {
          // Double-check still no subscribers after delay
          if (this.subscribers.size === 0) {
            console.log('[WebSocketManager] Disconnecting (no subscribers after delay)');
            this.disconnect();
          }
        }, 100);
      }
    };
  }

  /**
   * Send message through WebSocket
   */
  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocketManager] Cannot send message: WebSocket not connected');
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.disconnectTimer) {
      clearTimeout(this.disconnectTimer);
      this.disconnectTimer = null;
    }

    if (this.ws) {
      console.log('[WebSocketManager] Closing connection');
      this.ws.close();
      this.ws = null;
    }

    this.url = null;
    this.reconnectAttempts = 0;
  }

  /**
   * Get connection state
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const websocketManager = WebSocketManager.getInstance();
