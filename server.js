const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const PORT = process.env.PORT || 3457;
const API_PORT = 8080;

// MIME types
const mimeTypes = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon'
};

// Start Python API server
function startPythonAPI() {
    const pythonProcess = spawn('python3', ['-m', 'api.server'], {
        cwd: __dirname,
        env: { ...process.env, PORT: API_PORT.toString() }
    });
    
    pythonProcess.stdout.on('data', (data) => {
        console.log(`[API] ${data.toString().trim()}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
        console.error(`[API] ${data.toString().trim()}`);
    });
    
    pythonProcess.on('close', (code) => {
        console.log(`[API] Process exited with code ${code}`);
        // Restart after 5 seconds
        setTimeout(startPythonAPI, 5000);
    });
    
    return pythonProcess;
}

// Proxy API requests to Python
async function proxyToAPI(req, res) {
    const options = {
        hostname: 'localhost',
        port: API_PORT,
        path: req.url,
        method: req.method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const proxyReq = http.request(options, (proxyRes) => {
        res.writeHead(proxyRes.statusCode, proxyRes.headers);
        proxyRes.pipe(res);
    });
    
    proxyReq.on('error', (e) => {
        res.writeHead(502);
        res.end(JSON.stringify({ error: 'API unavailable', details: e.message }));
    });
    
    if (req.method === 'POST' || req.method === 'PUT') {
        req.pipe(proxyReq);
    } else {
        proxyReq.end();
    }
}

// Create HTTP server
const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const pathname = url.pathname;
    
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }
    
    // API routes - proxy to Python
    if (pathname.startsWith('/api/v1/')) {
        proxyToAPI(req, res);
        return;
    }
    
    // Health check
    if (pathname === '/api/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', service: 'vibeguard', version: '0.2.0' }));
        return;
    }
    
    // GitHub webhook
    if (pathname === '/webhook/github') {
        proxyToAPI(req, res);
        return;
    }
    
    // Static files
    let filePath = pathname === '/' ? '/index.html' : pathname;
    filePath = path.join(__dirname, 'web', filePath);
    
    const ext = path.extname(filePath);
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    
    fs.readFile(filePath, (err, content) => {
        if (err) {
            if (err.code === 'ENOENT') {
                // Try index.html for SPA routing
                fs.readFile(path.join(__dirname, 'web', 'index.html'), (err2, content2) => {
                    if (err2) {
                        res.writeHead(404);
                        res.end('Not found');
                    } else {
                        res.writeHead(200, { 'Content-Type': 'text/html' });
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

// Start servers
console.log('Starting VibeGuard...');
console.log(`[WEB] Starting on port ${PORT}`);
console.log(`[API] Starting on port ${API_PORT}`);

// Start Python API (disabled for now - use standalone)
// startPythonAPI();

server.listen(PORT, () => {
    console.log(`[WEB] Listening on http://localhost:${PORT}`);
    console.log(`\nVibeGuard is running!`);
    console.log(`  Landing page: http://localhost:${PORT}`);
    console.log(`  API: http://localhost:${PORT}/api/v1/`);
});
