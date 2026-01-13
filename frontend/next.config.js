/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const origin = process.env.BACKEND_ORIGIN || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${origin}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
