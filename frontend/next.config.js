/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Disable ESLint during production builds (Vercel deployment)
  eslint: {
    ignoreDuringBuilds: true,
  },

  // Also disable TypeScript type checking during builds
  typescript: {
    ignoreBuildErrors: true,
  },

  async rewrites() {
    const origin = process.env.BACKEND_ORIGIN || 'http://localhost:8003';
    return [
      {
        source: '/api/:path*',
        destination: `${origin}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
