import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  images: {
    // Allow local images from /public
    // No remote patterns needed since all figures are served locally
    unoptimized: false,
  },
};

export default nextConfig;
