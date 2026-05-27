// k6 load smoke for public optimize API (optional — install k6, set BASE_URL and API_KEY)
import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.BASE_URL || "http://localhost:8000";
const API_KEY = __ENV.API_KEY || "";

export const options = {
  vus: 2,
  duration: "30s",
  thresholds: {
    http_req_failed: ["rate<0.5"],
  },
};

export default function () {
  if (!API_KEY) {
    console.warn("Set API_KEY env var for meaningful results");
  }
  const r = http.post(
    `${BASE}/v1/optimize`,
    JSON.stringify({
      origin: "Denver, CO",
      destination: "Grand Junction, CO",
    }),
    {
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
      },
    }
  );
  check(r, { "202 or 401": (res) => res.status === 202 || res.status === 401 });
  sleep(0.5);
}
