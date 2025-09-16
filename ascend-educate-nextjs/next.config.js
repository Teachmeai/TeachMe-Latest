/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost'],
  },
  // Suppress hydration warnings for browser extensions
  reactStrictMode: true,
  swcMinify: true,
  // Add experimental features to help with hydration
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
}

module.exports = nextConfig
