import http.server


class RequestHandlerImpl(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)

        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        self.wfile.write("Hello World\n".encode("utf-8"))

    def do_POST(self):
        req_body = self.rfile.read(
            int(self.headers["Content-Length"])).decode()
        print(req_body)

        self.send_response(200)

        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        self.wfile.write(("Hello World: " + req_body + "\n").encode("utf-8"))


if __name__ == '__main__':
    server_address = ("0.0.0.0", 8000)
    httpd = http.server.HTTPServer(server_address, RequestHandlerImpl)

    httpd.serve_forever()
