import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/svelte";
import PageNavigator from "$lib/components/panels/PageNavigator.svelte";
import type { PageSummary } from "$lib/api/types";

// Mock $app/navigation goto
const mockGoto = vi.fn();
vi.mock("$app/navigation", () => ({
  goto: (...args: unknown[]) => mockGoto(...args),
}));

function makePages(count: number): PageSummary[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `page-${i + 1}`,
    page_no: i + 1,
    status: i === 0 ? "pending" : i === 1 ? "in_progress" : "reviewed",
  })) as PageSummary[];
}

describe("PageNavigator", () => {
  beforeEach(() => {
    mockGoto.mockClear();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders page buttons for each page", () => {
    const pages = makePages(5);
    render(PageNavigator, {
      props: { pages, currentPageId: "page-1" },
    });

    for (let i = 1; i <= 5; i++) {
      expect(screen.getByText(String(i))).toBeTruthy();
    }
  });

  it("shows current position (e.g. 1 / 5)", () => {
    const pages = makePages(5);
    render(PageNavigator, {
      props: { pages, currentPageId: "page-3" },
    });

    expect(screen.getByText("3 / 5")).toBeTruthy();
  });

  it("highlights current page button", () => {
    const pages = makePages(3);
    const { container } = render(PageNavigator, {
      props: { pages, currentPageId: "page-2" },
    });

    const buttons = container.querySelectorAll("button");
    // Find the page-2 button (button with text "2")
    const page2Button = Array.from(buttons).find(
      (b) => b.textContent?.trim() === "2",
    );
    expect(page2Button).toBeTruthy();
    expect(page2Button?.className).toContain("bg-primary-500");
  });

  it("navigates to a different page on click", async () => {
    const pages = makePages(3);
    render(PageNavigator, {
      props: { pages, currentPageId: "page-1" },
    });

    const page2Button = screen.getByText("2");
    await fireEvent.click(page2Button);

    expect(mockGoto).toHaveBeenCalledWith("/label/page-2");
  });

  it("does not navigate when clicking current page", async () => {
    const pages = makePages(3);
    render(PageNavigator, {
      props: { pages, currentPageId: "page-1" },
    });

    const page1Button = screen.getByText("1");
    await fireEvent.click(page1Button);

    expect(mockGoto).not.toHaveBeenCalled();
  });

  it("disables prev button on first page", () => {
    const pages = makePages(3);
    const { container } = render(PageNavigator, {
      props: { pages, currentPageId: "page-1" },
    });

    // Prev button is the first nav button (has the left arrow SVG)
    const prevButton = container.querySelector("button[disabled]");
    expect(prevButton).toBeTruthy();
  });

  it("disables next button on last page", () => {
    const pages = makePages(3);
    const { container } = render(PageNavigator, {
      props: { pages, currentPageId: "page-3" },
    });

    const disabledButtons = container.querySelectorAll("button[disabled]");
    expect(disabledButtons.length).toBeGreaterThanOrEqual(1);
  });

  it("prev button navigates to previous page", async () => {
    const pages = makePages(3);
    const { container } = render(PageNavigator, {
      props: { pages, currentPageId: "page-2" },
    });

    // The prev button has title containing "이전"
    const prevButton = container.querySelector(
      'button[title*="이전"]',
    ) as HTMLButtonElement;
    expect(prevButton).toBeTruthy();
    expect(prevButton.disabled).toBe(false);

    await fireEvent.click(prevButton);
    expect(mockGoto).toHaveBeenCalledWith("/label/page-1");
  });

  it("next button navigates to next page", async () => {
    const pages = makePages(3);
    const { container } = render(PageNavigator, {
      props: { pages, currentPageId: "page-2" },
    });

    const nextButton = container.querySelector(
      'button[title*="다음"]',
    ) as HTMLButtonElement;
    expect(nextButton).toBeTruthy();
    expect(nextButton.disabled).toBe(false);

    await fireEvent.click(nextButton);
    expect(mockGoto).toHaveBeenCalledWith("/label/page-3");
  });

  it("shows status summary badges", () => {
    const pages = makePages(5);
    const { container } = render(PageNavigator, {
      props: { pages, currentPageId: "page-1" },
    });

    // Should have status badges for non-zero counts
    const badges = container.querySelectorAll("span.text-\\[10px\\]");
    expect(badges.length).toBeGreaterThan(0);
  });
});
