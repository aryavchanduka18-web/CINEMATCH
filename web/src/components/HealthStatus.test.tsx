import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import HealthStatus from "./HealthStatus";

function renderWithClient() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <HealthStatus />
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

test("shows API and DB status from /api/health", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ status: "ok", db: "ok", version: "0.1.0" }), { status: 200 }),
  );
  renderWithClient();
  expect(await screen.findByText("API: ok, DB: ok")).toBeInTheDocument();
  expect(globalThis.fetch).toHaveBeenCalledWith("/api/health");
});

test("shows unreachable when the API is down", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("", { status: 500 }));
  renderWithClient();
  expect(await screen.findByText("API: unreachable")).toBeInTheDocument();
});