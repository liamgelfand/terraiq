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
  role: "admin" | "member";
  onboarding_completed: boolean;
  is_founder?: boolean;
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
  job_type?: string;
  time_budget_fraction: number;
  load_kg?: number;
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
  // sweep result fields (present when job_type === "sweep")
  curve?: SweepPoint[];
  baseline_fuel_L?: number;
  distance_km?: number;
}

export type JobStatus = "pending" | "running" | "completed" | "failed";

export interface Job {
  id: string;
  status: JobStatus;
  config: JobConfig;
  result: JobResult | null;
  error_message: string | null;
  error_code?: string | null;
  error_hint?: string | null;
  corridor_id?: string | null;
  batch_id?: string | null;
  simulation_engine_version?: string | null;
  lineage?: Record<string, unknown> | null;
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

export interface JobListPage {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
}

// ─── Fleet admin ────────────────────────────────────────────────────────────

export interface FleetUsage {
  jobs_total: number;
  jobs_completed: number;
  jobs_failed: number;
  jobs_this_month: number;
  api_key_usage_total: number;
  billing_plan: string;
  plan_label: string;
  jobs_limit_monthly: number | null;
  jobs_remaining_this_month: number | null;
  corridors_count: number;
  corridors_limit: number | null;
  stripe_configured: boolean;
}

export interface AuditEventRow {
  id: string;
  actor_user_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogPage {
  items: AuditEventRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface WebhookDeliveryRow {
  id: string;
  job_id: string;
  url: string;
  event: string;
  attempt: number;
  http_status: number | null;
  error_message: string | null;
  created_at: string;
}

export interface WebhookDeliveryPage {
  items: WebhookDeliveryRow[];
  total: number;
  page: number;
  page_size: number;
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

export async function forgotPassword(email: string): Promise<void> {
  await apiClient.post("/auth/forgot-password", { email });
}

export async function resetPassword(token: string, new_password: string): Promise<void> {
  await apiClient.post("/auth/reset-password", { token, new_password });
}

export async function updateProfile(full_name: string): Promise<CurrentUser> {
  const { data } = await apiClient.patch<CurrentUser>("/auth/me", { full_name });
  return data;
}

export async function updateFleetName(fleet_name: string): Promise<CurrentUser> {
  const { data } = await apiClient.patch<CurrentUser>("/auth/fleet", { fleet_name });
  return data;
}

export async function changePassword(current_password: string, new_password: string): Promise<void> {
  await apiClient.post("/auth/change-password", { current_password, new_password });
}

export async function updateOnboarding(onboarding_completed: boolean): Promise<CurrentUser> {
  const { data } = await apiClient.patch<CurrentUser>("/auth/onboarding", { onboarding_completed });
  return data;
}

export async function getInviteInfo(token: string): Promise<{ fleet_name: string; email: string }> {
  const { data } = await apiClient.get<{ fleet_name: string; email: string }>("/auth/invite-info", {
    params: { token },
  });
  return data;
}

export async function acceptInvite(token: string, full_name: string, new_password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/accept-invite", {
    token,
    full_name,
    new_password,
  });
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

export async function listJobs(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  q?: string;
}): Promise<JobListPage> {
  const { data } = await apiClient.get<JobListPage>("/api/jobs", { params });
  return data;
}

/** Download fleet job history as CSV (uses current JWT). */
export async function downloadJobsExport(): Promise<void> {
  const { data } = await apiClient.get<Blob>("/api/jobs/export.csv", {
    responseType: "blob",
  });
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = `terraiq-jobs-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function listVehicles(): Promise<Vehicle[]> {
  const { data } = await apiClient.get<Vehicle[]>("/api/vehicles");
  return data;
}

export async function fetchFleetUsage(): Promise<FleetUsage> {
  const { data } = await apiClient.get<FleetUsage>("/api/fleet/usage");
  return data;
}

export interface OnboardingStatus {
  corridors: number;
  completed_jobs: number;
  telemetry_uploads: number;
  starter_seeded: boolean;
  ready_for_brief: boolean;
}

export async function fetchOnboardingStatus(): Promise<OnboardingStatus> {
  const { data } = await apiClient.get<OnboardingStatus>("/api/fleet/onboarding-status");
  return data;
}

export interface LeadRow {
  id: string;
  name: string;
  email: string;
  company: string;
  fleet_size: string | null;
  message: string | null;
  source: string;
  status: string;
  created_at: string;
}

export async function fetchLeads(): Promise<LeadRow[]> {
  const { data } = await apiClient.get<LeadRow[]>("/api/leads");
  return data;
}

export async function updateLeadStatus(id: string, status: string): Promise<LeadRow> {
  const { data } = await apiClient.patch<LeadRow>(`/api/leads/${id}`, { status });
  return data;
}

export async function openAnalyticsReport(): Promise<void> {
  const { data } = await apiClient.get<Blob>("/api/analytics/report.html", { responseType: "blob" });
  const url = URL.createObjectURL(data);
  window.open(url, "_blank", "noopener");
}

export async function createFleetInvite(email: string): Promise<void> {
  await apiClient.post("/api/fleet/invites", { email });
}

export async function fetchAuditLog(page = 1, page_size = 25): Promise<AuditLogPage> {
  const { data } = await apiClient.get<AuditLogPage>("/api/fleet/audit-events", { params: { page, page_size } });
  return data;
}

export async function fetchWebhookDeliveries(page = 1, page_size = 25): Promise<WebhookDeliveryPage> {
  const { data } = await apiClient.get<WebhookDeliveryPage>("/api/fleet/webhook-deliveries", {
    params: { page, page_size },
  });
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

// ─── Pilot: corridors, batches, telemetry, ops ───────────────────────────────

export interface SavedCorridor {
  id: string;
  fleet_id: string;
  name: string;
  origin: string;
  destination: string;
  vehicle_id: string;
  load_kg: number | null;
  time_budget_fraction: number;
  created_at: string;
  updated_at: string;
}

export interface JobBatchRow {
  id: string;
  fleet_id: string;
  name: string | null;
  status: string;
  config: Record<string, unknown>;
  summary: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface BatchListResponse {
  items: JobBatchRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface TelemetryUploadRow {
  id: string;
  fleet_id: string;
  job_id: string | null;
  corridor_id: string | null;
  original_filename: string;
  row_count: number;
  status: string;
  adherence: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TelemetryListResponse {
  items: TelemetryUploadRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface OpsBoardRow {
  corridor_id: string;
  corridor_name: string;
  origin: string;
  destination: string;
  last_job_id: string | null;
  last_job_status: string | null;
  last_job_completed_at: string | null;
  fuel_saved_liters: number | null;
  fuel_saved_pct: number | null;
  cost_saved_usd: number | null;
  adherence_pct: number | null;
}

export async function fetchCorridors(): Promise<SavedCorridor[]> {
  const { data } = await apiClient.get<SavedCorridor[]>("/api/corridors");
  return data;
}

export async function createCorridor(body: {
  name: string;
  origin: string;
  destination: string;
  vehicle_id?: string;
  load_kg?: number;
  time_budget_fraction?: number;
}): Promise<SavedCorridor> {
  const { data } = await apiClient.post<SavedCorridor>("/api/corridors", body);
  return data;
}

export async function duplicateCorridor(id: string): Promise<SavedCorridor> {
  const { data } = await apiClient.post<SavedCorridor>(`/api/corridors/${id}/duplicate`);
  return data;
}

export async function deleteCorridor(id: string): Promise<void> {
  await apiClient.delete(`/api/corridors/${id}`);
}

export async function createJobBatch(corridor_ids: string[], name?: string): Promise<JobBatchRow> {
  const { data } = await apiClient.post<JobBatchRow>("/api/batches", { corridor_ids, name });
  return data;
}

export async function listJobBatches(page = 1): Promise<BatchListResponse> {
  const { data } = await apiClient.get<BatchListResponse>("/api/batches", { params: { page } });
  return data;
}

export async function fetchOpsBoard(): Promise<OpsBoardRow[]> {
  const { data } = await apiClient.get<OpsBoardRow[]>("/api/pilot/ops-board");
  return data;
}

export async function listTelemetryUploads(page = 1): Promise<TelemetryListResponse> {
  const { data } = await apiClient.get<TelemetryListResponse>("/api/telemetry", { params: { page } });
  return data;
}

export async function submitTelemetryUpload(file: File, jobId: string, corridorId?: string): Promise<TelemetryUploadRow> {
  const form = new FormData();
  form.append("file", file);
  const params = new URLSearchParams({ job_id: jobId });
  if (corridorId) params.set("corridor_id", corridorId);
  const { data } = await apiClient.post<TelemetryUploadRow>(
    `/api/telemetry?${params.toString()}`,
    form,
    {
      transformRequest: [
        (body, headers) => {
          if (body instanceof FormData) {
            delete headers["Content-Type"];
          }
          return body;
        },
      ],
    }
  );
  return data;
}

export async function downloadPilotPackageCsv(): Promise<void> {
  const { data } = await apiClient.get<Blob>("/api/pilot/export-package.csv", { responseType: "blob" });
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = `terraiq-pilot-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function fetchFleetDataExport(): Promise<Record<string, unknown>> {
  const { data } = await apiClient.get<Record<string, unknown>>("/api/fleet/data-export");
  return data;
}

export async function purgeFleetData(includeJobs: boolean): Promise<void> {
  await apiClient.delete("/api/fleet/data-purge", { data: { include_jobs: includeJobs } });
}

export async function startBillingCheckout(): Promise<{ url: string }> {
  const { data } = await apiClient.post<{ url: string }>("/api/billing/checkout-session");
  return data;
}

export async function startBillingPortal(): Promise<{ url: string }> {
  const { data } = await apiClient.post<{ url: string }>("/api/billing/portal-session");
  return data;
}

export interface DriverBriefPayload {
  job_id: string;
  route: string;
  origin?: string;
  destination?: string;
  vehicle_id?: string | null;
  fleet_name: string;
  savings?: {
    fuel_saved_liters?: number;
    fuel_saved_pct?: number;
    cost_saved_usd?: number;
  };
  brief: {
    segments: Array<{
      start_km: number;
      end_km: number;
      target_speed_kmh: number;
      target_speed_mph?: number;
      summary: string;
    }>;
    distance_km?: number;
    segment_count?: number;
  };
}

export async function fetchDriverBrief(jobId: string): Promise<DriverBriefPayload> {
  const { data } = await apiClient.get<DriverBriefPayload>(`/api/pilot/jobs/${jobId}/driver-brief`);
  return data;
}

export async function submitDemoRequest(body: {
  name: string;
  email: string;
  company: string;
  fleet_size?: string;
  message?: string;
}): Promise<{ ok: boolean }> {
  const { data } = await apiClient.post<{ ok: boolean }>("/api/public/demo-request", body);
  return data;
}
