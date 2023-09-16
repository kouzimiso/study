from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class MyRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            user_message = data.get('message')
            print(user_message)
            
            response = {'message': '受信文字列: ' + user_message}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # クロスオリジンリクエストを許可する設定
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_error(404)
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Allow', 'POST, OPTIONS')
        self.send_header('Content-Length', '0')
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

def run(server_class=HTTPServer, handler_class=MyRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Server running at localhost:8000...')
    httpd.serve_forever()

run()
