/** @type {import('next').NextConfig} */
const webpack = require('webpack');

const nextConfig = {
  reactStrictMode: true,
  // Allow connecting to Gradio backend (adjust port if needed)
  async rewrites() {
    return [
      {
        source: '/api/gradio/:path*',
        destination: 'http://localhost:7860/:path*',
      },
    ];
  },
  webpack: (config, { isServer }) => {
    // Handle Node.js built-in modules for client-side
    if (!isServer) {
      // Transform node: protocol imports to regular module names
      config.plugins = [
        ...config.plugins,
        new webpack.NormalModuleReplacementPlugin(
          /^node:/,
          (resource) => {
            resource.request = resource.request.replace(/^node:/, '');
          }
        ),
      ];
      
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        stream: false,
        url: false,
        zlib: false,
        http: false,
        https: false,
        assert: false,
        os: false,
        path: false,
        buffer: require.resolve('buffer/'),
      };
      
      // Add buffer polyfill
      config.plugins.push(
        new webpack.ProvidePlugin({
          Buffer: ['buffer', 'Buffer'],
        })
      );
    }
    
    return config;
  },
};

module.exports = nextConfig;

