/**
 * Tests for the Register page component.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { Register } from "../pages/Register";

const mockRegister = vi.fn();
vi.mock("../contexts/AuthContext", () => ({
  useAuth: () => ({ register: mockRegister }),
}));

const noop = () => {};

function renderRegister(overrides?: { onGoLogin?: () => void }) {
  return render(<Register onGoLogin={overrides?.onGoLogin ?? noop} />);
}

describe("Register", () => {
  beforeEach(() => mockRegister.mockReset());

  it("renders all required fields", () => {
    renderRegister();
    expect(screen.getByPlaceholderText(/alex johnson/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/acme logistics/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/you@fleet\.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/)).toBeInTheDocument();
  });

  it("calls register with all form values on submit", async () => {
    mockRegister.mockResolvedValueOnce(undefined);
    renderRegister();

    await userEvent.type(screen.getByPlaceholderText(/alex johnson/i), "Jane Doe");
    await userEvent.type(screen.getByPlaceholderText(/acme logistics/i), "Acme Fleet");
    await userEvent.type(screen.getByPlaceholderText(/you@fleet\.com/i), "jane@acme.com");
    await userEvent.type(screen.getByPlaceholderText(/••••••••/), "password123");
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() =>
      expect(mockRegister).toHaveBeenCalledWith(
        "jane@acme.com",
        "password123",
        "Jane Doe",
        "Acme Fleet"
      )
    );
  });

  it("shows an inline email error when 409 is returned", async () => {
    mockRegister.mockRejectedValueOnce({
      response: { status: 409, data: { detail: "Email already registered" } },
    });
    renderRegister();

    await userEvent.type(screen.getByPlaceholderText(/alex johnson/i), "X");
    await userEvent.type(screen.getByPlaceholderText(/acme logistics/i), "Y");
    await userEvent.type(screen.getByPlaceholderText(/you@fleet\.com/i), "dup@x.com");
    await userEvent.type(screen.getByPlaceholderText(/••••••••/), "password123");
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() =>
      expect(screen.getByText(/already exists/i)).toBeInTheDocument()
    );
  });

  it("clears email error when user types in email field", async () => {
    mockRegister.mockRejectedValueOnce({
      response: { status: 409, data: { detail: "Email already registered" } },
    });
    renderRegister();

    await userEvent.type(screen.getByPlaceholderText(/alex johnson/i), "X");
    await userEvent.type(screen.getByPlaceholderText(/acme logistics/i), "Y");
    await userEvent.type(screen.getByPlaceholderText(/you@fleet\.com/i), "dup@x.com");
    await userEvent.type(screen.getByPlaceholderText(/••••••••/), "password123");
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => screen.getByText(/already exists/i));

    await userEvent.type(screen.getByPlaceholderText(/you@fleet\.com/i), "a");
    expect(screen.queryByText(/already exists/i)).not.toBeInTheDocument();
  });

  it("calls onGoLogin when 'Sign in' is clicked", async () => {
    const onGoLogin = vi.fn();
    renderRegister({ onGoLogin });
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));
    expect(onGoLogin).toHaveBeenCalledOnce();
  });
});
