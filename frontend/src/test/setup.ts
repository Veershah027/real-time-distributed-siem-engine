import "@testing-library/jest-dom/vitest";

// jsdom has no WebSocket; provide a no-op stub for hooks under test.
class FakeWebSocket {
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  close() {}
  send() {}
}
// @ts-expect-error - test shim
globalThis.WebSocket = FakeWebSocket;
