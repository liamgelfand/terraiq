import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { Landing } from "../pages/Landing";

vi.mock("../api/client", () => ({
  submitDemoRequest: vi.fn(),
}));

describe("Landing", () => {
  it("renders the product headline and CTAs", () => {
    render(
      <Landing onSignIn={() => {}} onRegister={() => {}} onLegal={() => {}} />
    );
    expect(screen.getByRole("heading", { name: /tell the truck how fast/i })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /sign in/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: /create account/i }).length).toBeGreaterThan(0);
  });

  it("calls onSignIn from the header", async () => {
    const onSignIn = vi.fn();
    render(<Landing onSignIn={onSignIn} onRegister={() => {}} onLegal={() => {}} />);
    await userEvent.click(screen.getAllByRole("button", { name: /^sign in$/i })[0]);
    expect(onSignIn).toHaveBeenCalled();
  });

  it("opens legal pages from the footer", async () => {
    const onLegal = vi.fn();
    render(<Landing onSignIn={() => {}} onRegister={() => {}} onLegal={onLegal} />);
    await userEvent.click(screen.getByRole("button", { name: /^terms$/i }));
    expect(onLegal).toHaveBeenCalledWith("terms");
  });
});
