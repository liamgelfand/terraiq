import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// Attach JWT from localStorage on every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("tiq_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Auth types ───────────────────────────────────────────────────────────────

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  fleet_id: string;
  fleet_name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// ─── Job types ────────────────────────────────────────────────────────────────

export interface JobConfig {
  origin: string;
  destination: string;
  vehicle_id: string;
  time_budget_fraction: number;
}

export interface SimulationResult {
  route_name: string;
  total_distance_km: number;
  elevation_gain_m: number;
  elevation_loss_m: number;
  total_fuel_liters: number;
  total_fuel_kg: number;
  fuel_per_100km: number;
  vehicle_name: string;
  speed_profile_ms: number[];
  distances_m: number[];
  elevations_m: number[];
  grades: number[];
  speed_limits_ms: number[];
  segment_fuel_L: number[];
  segment_power_kw: number[];
  lat: number[];
  lon: number[];
}

export interface Savings {
  fuel_saved_liters: number;
  fuel_saved_pct: number;
  cost_saved_usd: number;
  co2_saved_kg: number;
}

export interface JobResult {
  baseline: SimulationResult;
  optimized: SimulationResult;
  savings: Savings;
}

export type JobStatus = "pending" | "running" | "completed" | "failed";

export interface Job {
  id: string;
  status: JobStatus;
  config: JobConfig;
  result: JobResult | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface Vehicle {
  id: string;
  name: string;
  type: string;
  mass_kg: number;
  max_speed_kmh: number;
  description: string;
}

// ─── API key types ────────────────────────────────────────────────────────────

export interface ApiKey {
  id: string;
  name: string;
  fleet_name: string | null;
  key_prefix: string;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiKeyCreated extends ApiKey {
  raw_key: string;
}

// ─── Analytics types ──────────────────────────────────────────────────────────

export interface AnalyticsSummary {
  total_jobs: number;
  completed_jobs: number;
  total_fuel_saved_L: number;
  total_cost_saved_usd: number;
  total_co2_saved_kg: number;
  total_distance_km: number;
}

// ─── Sweep types ──────────────────────────────────────────────────────────────

export interface SweepPoint {
  time_budget_fraction: number;
  extra_time_min: number;
  fuel_saved_L: number;
  fuel_saved_pct: number;
  cost_saved_usd: number;
  co2_saved_kg: number;
}

export interface SweepResult {
  distance_km: number;
  baseline_fuel_L: number;
  curve: SweepPoint[];
}

export type SweepStatus = "pending" | "running" | "completed" | "failed";

export interface SweepJob {
  job_id: string;
  status: SweepStatus;
  created_at: string;
  completed_at: string | null;
  poll_url: string;
  result: SweepResult | null;
  error: string | null;
}

// ─── Auth API ─────────────────────────────────────────────────────────────────

export async function register(
  email: string,
  password: string,
  full_name: string,
  fleet_name: string
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/register", {
    email,
    password,
    full_name,
    fleet_name,
  });
  return data;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", { email, password });
  return data;
}

export async function getMe(): Promise<CurrentUser> {
  const { data } = await apiClient.get<CurrentUser>("/auth/me");
  return data;
}

// ─── Jobs API ─────────────────────────────────────────────────────────────────

export async function submitJob(config: JobConfig): Promise<Job> {
  const { data } = await apiClient.post<Job>("/api/jobs", { config });
  return data;
}

export async function getJob(jobId: string): Promise<Job> {
  const { data } = await apiClient.get<Job>(`/api/jobs/${jobId}`);
  return data;
}

export async function listJobs(): Promise<Job[]> {
  const { data } = await apiClient.get<Job[]>("/api/jobs");
  return data;
}

export async function listVehicles(): Promise<Vehicle[]> {
  const { data } = await apiClient.get<Vehicle[]>("/api/vehicles");
  return data;
}

// ─── API Keys API ─────────────────────────────────────────────────────────────

export async function fetchKeys(): Promise<ApiKey[]> {
  const { data } = await apiClient.get<ApiKey[]>("/api/keys");
  return data;
}

export async function createKey(name: string): Promise<ApiKeyCreated> {
  const { data } = await apiClient.post<ApiKeyCreated>("/api/keys", { name });
  return data;
}

export async function revokeKey(id: string): Promise<void> {
  await apiClient.delete(`/api/keys/${id}`);
}

// ─── Analytics API ────────────────────────────────────────────────────────────

export async function fetchAnalytics(): Promise<AnalyticsSummary> {
  const { data } = await apiClient.get<AnalyticsSummary>("/api/analytics");
  return data;
}

// ─── Sweep API ────────────────────────────────────────────────────────────────

export async function submitSweep(
  origin: string,
  destination: string,
  apiKey: string
): Promise<SweepJob> {
  const { data } = await apiClient.post<SweepJob>(
    "/v1/sweep",
    { origin, destination },
    { headers: { "X-API-Key": apiKey } }
  );
  return data;
}

export async function getSweep(jobId: string, apiKey: string): Promise<SweepJob> {
  const { data } = await apiClient.get<SweepJob>(`/v1/sweep/${jobId}`, {
    headers: { "X-API-Key": apiKey },
  });
  return data;
}
