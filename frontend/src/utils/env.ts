import { OpenAPI } from "@/client"

/**
 * Returns the WebSocket base URL (e.g., wss://api.example.com or ws://localhost:8000)
 * derived from the current API configuration or window location.
 *
 * Logic:
 * 1. If OpenAPI.BASE is set:
 *    - Converts http(s) -> ws(s)
 *    - Strips common API prefixes (/api/v1) to get the root URL where /ws is mounted
 * 2. If OpenAPI.BASE is not set:
 *    - Falls back to current window location protocol/host
 */
export const getWebSocketBaseUrl = (): string => {
  const apiBase = OpenAPI.BASE

  // Fallback if not configured
  if (!apiBase) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    return `${protocol}//${window.location.host}`
  }

  try {
    // Handle relative URLs by basing them on window.location
    const url = new URL(apiBase, window.location.href)

    // Swap protocol
    if (url.protocol === "https:") {
      url.protocol = "wss:"
    } else if (url.protocol === "http:") {
      url.protocol = "ws:"
    }

    // Strip common API prefixes
    // The backend mounts websockets at /ws (root level usually),
    // while API is at /api/v1.
    // We want the base URL that we can append /ws/... to.

    // Remove trailing slash
    let pathname = url.pathname
    if (pathname.endsWith("/")) {
      pathname = pathname.slice(0, -1)
    }

    // Remove /api/v1 suffix
    if (pathname.endsWith("/api/v1")) {
      pathname = pathname.slice(0, -"/api/v1".length)
    } else if (pathname.endsWith("/api")) {
      pathname = pathname.slice(0, -"/api".length)
    }

    url.pathname = pathname

    // Return the origin + path (which should be empty or base path)
    // We do NOT append /ws here, caller does that.
    return url.toString().replace(/\/$/, "")
  } catch (e) {
    console.error("Failed to parse OpenAPI.BASE for WebSocket URL", e)
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    return `${protocol}//${window.location.host}`
  }
}
