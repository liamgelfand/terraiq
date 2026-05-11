/**
 * Tests for the Login page component.
 * The AuthContext is mocked so no real API calls are made.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { Login } from "../pages/Login";

// ── Mock AuthContext ──────────────────────────────────────────────────────────

const mockLogin = vi.fn();
vi.mock("../contexts/AuthContext", () => ({
  useAuth: () => ({ login: mockLogin }),
}));

const noop = () => {};

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderLogin(overrides?: { onGoRegister?: () => void; onForgotPassword?: () => void }) {
  return render(
    <Login
      onGoRegister={overrides?.onGoRegister ?? noop}
      onForgotPassword={overrides?.onForgotPassword ?? noop}
    />
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("Login", () => {
  beforeEach(() => mockLogin.mockReset());

  it("renders email and password fields", () => {
    renderLogin();
    expect(screen.getByPlaceholderText(/you@fleet\.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/)).toBeInTheDocument();
  });

  it("renders a sign-in button", () => {
    renderLogin();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("calls login with entered credentials on submit", async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText(/you@fleet\.com/i), "user@fleet.com");
    await userEvent.type(screen.getByPlaceholderText(/••••••••/), "password123");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(mockLogin).toHaveBeenCalledWith("user@fleet.com", "password123")
    );
  });

  it("shows error message on login failure", async () => {
    mockLogin.mockRejectedValueOnce({
      response: { data: { detail: "Invalid credentials" } },
    });
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText(/you@fleet\.com/i), "x@x.com");
    await userEvent.type(screen.getByPlaceholderText(/••••••••/), "wrong");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    );
  });

  it("calls onGoRegister when 'Create one' is clicked", async () => {
    const onGoRegister = vi.fn();
    renderLogin({ onGoRegister });
    await userEvent.click(screen.getByRole("button", { name: /create one/i }));
    expect(onGoRegister).toHaveBeenCalledOnce();
  });

  it("calls onForgotPassword when 'Forgot password?' is clicked", async () => {
    const onForgotPassword = vi.fn();
    renderLogin({ onForgotPassword });
    await userEvent.click(screen.getByRole("button", { name: /forgot password/i }));
    expect(onForgotPassword).toHaveBeenCalledOnce();
  });

  it("disables submit while loading", async () => {
    // login never resolves so the loading state persists
    mockLogin.mockImplementationOnce(() => new Promise(() => {}));
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText(/you@fleet\.com/i), "x@x.com");
    await userEvent.type(screen.getByPlaceholderText(/••••••••/), "pass1234");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /signing in/i })).toBeDisabled()
    );
  });
});
