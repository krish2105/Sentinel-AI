import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SeverityBadge, VerdictChip } from "@/components/primitives";

describe("SeverityBadge", () => {
  it("renders the severity label", () => {
    render(<SeverityBadge severity="CRITICAL" />);
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
  });
  it("falls back gracefully for unknown severity", () => {
    render(<SeverityBadge severity="WAT" />);
    expect(screen.getByText("WAT")).toBeInTheDocument();
  });
});

describe("VerdictChip", () => {
  it("renders the canonical label for a verdict", () => {
    render(<VerdictChip verdict="HIJACKED" />);
    expect(screen.getByText("HIJACKED")).toBeInTheDocument();
  });
  it("maps unknown verdicts to the SAFE style label", () => {
    render(<VerdictChip verdict="NONSENSE" />);
    expect(screen.getByText("SAFE")).toBeInTheDocument();
  });
});
