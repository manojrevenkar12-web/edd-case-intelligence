import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../src/app/App";
import data from "../public/data/dashboard.json";

function serve(body: unknown, ok = true) {
  vi.stubGlobal("fetch", vi.fn(async () => ({ ok, status: ok ? 200 : 500, json: async () => body })));
}

afterEach(() => vi.unstubAllGlobals());

describe("dashboard", () => {
  it("shows a skeleton while loading", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    render(<App />);
    expect(screen.getByRole("status", { name: /loading results/i })).toBeInTheDocument();
  });

  it("shows an error and loads again on retry", async () => {
    serve({}, false);
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/could not be loaded/);
    serve(data);
    await userEvent.click(screen.getByRole("button", { name: /load again/i }));
    expect(await screen.findByRole("heading", { name: /seven hypotheses/i })).toBeInTheDocument();
  });

  it("renders the held-out results and every section", async () => {
    serve(data);
    render(<App />);
    expect(await screen.findByText("91.3%")).toBeInTheDocument();
    for (const h of [/twelve weeks/i, /before they reach the team/i, /where the labels come from/i]) {
      expect(screen.getByRole("heading", { name: h })).toBeInTheDocument();
    }
  });

  it("says so when no experiments are registered", async () => {
    serve({ ...data, experiments: [] });
    render(<App />);
    expect(await screen.findByText(/no experiments registered/i)).toBeInTheDocument();
  });
});
