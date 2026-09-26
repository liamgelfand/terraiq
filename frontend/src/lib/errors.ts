/** Normalize FastAPI / axios errors, including 402 quota payloads. */
export function extractApiError(err: unknown, fallback = "Something went wrong. Try again."): string {
  if (typeof err !== "object" || err === null || !("response" in err)) {
    return fallback;
  }
  const detail = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && "message" in detail) {
    const msg = (detail as { message?: unknown }).message;
    if (typeof msg === "string") return msg;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg: string }).msg) : String(d)))
      .join("; ");
  }
  return fallback;
}
