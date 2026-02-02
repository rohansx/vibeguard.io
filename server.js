const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3457;

const mimeTypes = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);
  
  // API routes
  if (req.url.startsWith('/api/')) {
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Access-Control-Allow-Origin', '*');
    
    if (req.url === '/api/health') {
      res.writeHead(200);
      res.end(JSON.stringify({ status: 'ok', service: 'vibeguard' }));
      return;
    }
    
    if (req.url === '/api/v1/scan' && req.method === 'POST') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        // Mock scan response
        res.writeHead(200);
        res.end(JSON.stringify({
          status: 'completed',
          files_scanned: 12,
          ai_detected: 2,
          human_written: 10,
          results: [
            { file: 'src/auth/login.ts', ai_probability: 0.94, status: 'ai-generated' },
            { file: 'src/utils/parse.ts', ai_probability: 0.87, status: 'ai-generated' },
            { file: 'src/config/env.ts', ai_probability: 0.12, status: 'human-written' }
          ],
          policy_violations: 1,
          blocked: true,
          reason: 'AI code requires senior review'
        }));
      });
      return;
    }
    
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not found' }));
    return;
  }
  
  // Static files
  let filePath = req.url === '/' ? '/web/index.html' : '/web' + req.url;
  filePath = path.join(__dirname, filePath);
  
  const ext = path.extname(filePath);
  const contentType = mimeTypes[ext] || 'application/octet-stream';
  
  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // Try without /web prefix for direct file access
        const altPath = path.join(__dirname, req.url);
        fs.readFile(altPath, (err2, content2) => {
          if (err2) {
            res.writeHead(404);
            res.end('Not found');
          } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content2);
          }
        });
      } else {
        res.writeHead(500);
        res.end('Server error');
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    }
  });
});

server.listen(PORT, () => {
  console.log(`🛡️  VibeGuard running on http://localhost:${PORT}`);
});
