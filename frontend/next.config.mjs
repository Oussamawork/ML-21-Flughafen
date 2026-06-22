/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone", // self-contained server build for the Docker image (TDD-09)
};

export default nextConfig;
