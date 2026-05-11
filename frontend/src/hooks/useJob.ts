import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getJob, submitJob, type Job, type JobConfig } from "../api/client";

export function useSubmitJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: JobConfig) => submitJob(config),
    onSuccess: (job) => {
      queryClient.setQueryData(["job", job.id], job);
    },
  });
}

export function useJob(jobId: string | null) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = (query.state.data as Job | undefined)?.status;
      return status === "pending" || status === "running" ? 2000 : false;
    },
  });
}

export function useSubmitSweep() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: Pick<JobConfig, "origin" | "destination" | "vehicle_id">) =>
      submitJob({ ...config, job_type: "sweep", time_budget_fraction: 1.0 }),
    onSuccess: (job) => {
      queryClient.setQueryData(["job", job.id], job);
    },
  });
}
