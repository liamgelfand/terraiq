import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// ─── Types ────────────────────────────────────────────────────────────────────

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

// ─── API functions ────────────────────────────────────────────────────────────

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
