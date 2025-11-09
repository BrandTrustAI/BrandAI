import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export', // Static export for SPA
  images: {
    unoptimized: true, // Required for static export
  },
  trailingSlash: true,
};

export default nextConfig;
