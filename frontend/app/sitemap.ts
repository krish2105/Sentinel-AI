import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://sentinel-ai.vercel.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ["", "/dashboard", "/targets", "/proxy", "/model-card", "/auth"];
  return routes.map((path) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency: "weekly",
    priority: path === "" ? 1 : 0.7,
  }));
}
