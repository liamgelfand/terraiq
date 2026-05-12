/**
 * Tests for the RouteForm component.
 *
 * The API client (listVehicles) is mocked so no HTTP calls happen.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouteForm } from "../components/RouteForm";
import type { JobConfig } from "../api/client";

// ── Mock API client ────────────────────────────────────────────────────────────

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return {
    ...actual,
    listVehicles: vi.fn().mockResolvedValue([
      {
        id: "freightliner_2022",
        name: "Freightliner Cascadia 2022",
        type: "Class 8 Semi-Truck",
        mass_kg: 36287,
        max_speed_kmh: 105,
        description: "Test vehicle",
      },
    ]),
  };
});

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderForm(props?: Partial<Parameters<typeof RouteForm>[0]>) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onSubmit = vi.fn();
  render(
    <QueryClientProvider client={qc}>
      <RouteForm onSubmit={onSubmit} isLoading={false} {...props} />
    </QueryClientProvider>
  );
  return { onSubmit };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("RouteForm", () => {
  it("renders origin and destination inputs", () => {
    renderForm();
    expect(screen.getByPlaceholderText(/denver/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/grand junction/i)).toBeInTheDocument();
  });

  it("renders the payload weight input", () => {
    renderForm();
    expect(screen.getByLabelText(/payload weight/i)).toBeInTheDocument();
  });

  it("renders time budget slider when not in sweep mode", () => {
    renderForm({ sweepMode: false });
    expect(screen.getByText(/time budget/i)).toBeInTheDocument();
  });

  it("hides time budget slider in sweep mode", () => {
    renderForm({ sweepMode: true });
    expect(screen.queryByText(/time budget/i)).not.toBeInTheDocument();
  });

  it("submit button is disabled when fields are empty", () => {
    renderForm();
    expect(screen.getByRole("button", { name: /run simulation/i })).toBeDisabled();
  });

  it("submit button is enabled when origin and destination are filled", async () => {
    renderForm();
    await userEvent.type(screen.getByPlaceholderText(/e\.g\. denver/i), "Denver, CO");
    await userEvent.type(screen.getByPlaceholderText(/e\.g\. grand junction/i), "Grand Junction, CO");
    expect(screen.getByRole("button", { name: /run simulation/i })).not.toBeDisabled();
  });

  it("calls onSubmit with correct config including load_kg", async () => {
    const { onSubmit } = renderForm();
    await userEvent.type(screen.getByPlaceholderText(/e\.g\. denver/i), "Denver, CO");
    await userEvent.type(screen.getByPlaceholderText(/e\.g\. grand junction/i), "Grand Junction, CO");
    await userEvent.clear(screen.getByLabelText(/payload weight/i));
    await userEvent.type(screen.getByLabelText(/payload weight/i), "5000");
    fireEvent.click(screen.getByRole("button", { name: /run simulation/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledOnce());
    const config: JobConfig = onSubmit.mock.calls[0][0];
    expect(config.origin).toBe("Denver, CO");
    expect(config.destination).toBe("Grand Junction, CO");
    expect(config.load_kg).toBe(5000);
    expect(config.job_type).toBe("optimize");
  });

  it("applies preset route on button click", async () => {
    renderForm();
    const preset = screen.getByRole("button", { name: /denver.*grand junction/i });
    await userEvent.click(preset);
    expect((screen.getByPlaceholderText(/e\.g\. denver/i) as HTMLInputElement).value).toBe(
      "Denver, CO"
    );
  });

  it("shows 'Run Sweep' button text in sweep mode", () => {
    renderForm({ sweepMode: true });
    expect(screen.getByRole("button", { name: /run sweep/i })).toBeInTheDocument();
  });

  it("shows loading state when isLoading is true", () => {
    renderForm({ isLoading: true });
    expect(screen.getByRole("button", { name: /running simulation/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /running simulation/i })).toBeDisabled();
  });
});
