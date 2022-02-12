const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  app.use(
    createProxyMiddleware('/socket.io/', {
      target: 'http://localhost:3001',
      changeOrigin: true,
      ws: true,
      logLevel: 'debug',
    }),
  );
};
