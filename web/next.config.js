/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: {
      bodySizeLimit: "20mb", // PGN uploads can be a few MB
    },
  },
};

module.exports = nextConfig;
