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
  // Configure server actions body size limit for file uploads
  serverActions: {
    bodySizeLimit: '10mb', // Allow up to 10MB for file uploads
  },
}

module.exports = nextConfig
