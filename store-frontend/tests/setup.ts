import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

afterEach(() => cleanup());

// "server-only" throws outside React Server Components; tests import some of those modules directly.
vi.mock("server-only", () => ({}));
