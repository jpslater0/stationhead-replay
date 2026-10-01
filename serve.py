# http.server has no Range support, so <audio> cannot seek. This adds it.
import http.server, os, re, socketserver, threading
class H(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        rng = self.headers.get('Range')
        if not rng: return super().send_head()
        path = self.translate_path(self.path)
        if not os.path.isfile(path): return super().send_head()
        size = os.path.getsize(path)
        m = re.match(r'bytes=(\d*)-(\d*)', rng)
        start = int(m.group(1)) if m.group(1) else 0
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end: start = 0
        f = open(path, 'rb'); f.seek(start)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end - start + 1))
        self.end_headers()
        self._limit = end - start + 1
        return f
    def copyfile(self, src, dst):
        if self.headers.get('Range'):
            remaining = self._limit
            while remaining > 0:
                chunk = src.read(min(64 * 1024, remaining))
                if not chunk: break
                dst.write(chunk); remaining -= len(chunk)
        else:
            super().copyfile(src, dst)
class S(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
S(('', 8791), H).serve_forever()
