/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      // Note: WebSocket connections are handled directly by the client
      // connecting to ws://localhost:8000/ws
    ]
  },
}

module.exports = nextConfig
