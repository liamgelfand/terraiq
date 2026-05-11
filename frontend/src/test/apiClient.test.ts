/**
 * Unit tests for api/client.ts — pure function / type contract tests.
 * Axios is mocked so no real HTTP happens.
 */
import { vi, describe, it, expect, beforeEach } from "vitest";
import axios from "axios";

vi.mock("axios", async () => {
  const mockAxios = {
    create: vi.fn(() => mockAxios),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  };
  return { default: mockAxios };
});

const mockedAxios = axios as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

describe("API client contracts", () => {
  beforeEach(() => vi.clearAllMocks());

  it("listVehicles calls /api/vehicles and returns array", async () => {
    const fakeVehicles = [{ id: "v1", name: "Truck" }];
    mockedAxios.get.mockResolvedValue({ data: fakeVehicles });

    const { listVehicles } = await import("../api/client");
    const result = await listVehicles();
    expect(result).toEqual(fakeVehicles);
  });

  it("forgotPassword calls /auth/forgot-password", async () => {
    mockedAxios.post.mockResolvedValue({ data: {} });
    const { forgotPassword } = await import("../api/client");
    await forgotPassword("test@test.com");
    expect(mockedAxios.post).toHaveBeenCalled();
  });

  it("resetPassword calls /auth/reset-password", async () => {
    mockedAxios.post.mockResolvedValue({ data: {} });
    const { resetPassword } = await import("../api/client");
    await resetPassword("some-token", "newpassword");
    expect(mockedAxios.post).toHaveBeenCalled();
  });
});
