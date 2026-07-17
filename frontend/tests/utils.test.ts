import { describe, expect, it } from "vitest";
import { cn, scoreColor, timeAgo } from "@/lib/utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("a", "b")).toBe("a b");
  });
  it("dedupes conflicting tailwind classes (last wins)", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });
  it("drops falsy values", () => {
    expect(cn("a", false, null, undefined, "b")).toBe("a b");
  });
});

describe("scoreColor", () => {
  it("is teal for strong posture", () => {
    expect(scoreColor(90)).toBe("#22E9D3");
    expect(scoreColor(80)).toBe("#22E9D3");
  });
  it("is amber for middling posture", () => {
    expect(scoreColor(55)).toBe("#FFB020");
  });
  it("is red for weak posture", () => {
    expect(scoreColor(40)).toBe("#FF4D5E");
  });
});

describe("timeAgo", () => {
  it("returns 'just now' for the present", () => {
    expect(timeAgo(new Date().toISOString())).toBe("just now");
  });
  it("formats minutes and hours", () => {
    const t = (ms: number) => timeAgo(new Date(Date.now() - ms).toISOString());
    expect(t(5 * 60_000)).toBe("5m ago");
    expect(t(3 * 3_600_000)).toBe("3h ago");
    expect(t(2 * 86_400_000)).toBe("2d ago");
  });
});
