import http.server
import re
import logging
import time
import json

from torch.utils.tensorboard import SummaryWriter

from client import LoadMonitorClient
from rl import Agent

ADDRESS = "0.0.0.0"
PORT = 8000

logging.basicConfig(filename='log.txt',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s-%(funcName)s',
                    level=logging.INFO)


def run():
    run_name = f"K8s_{int(time.time())}"
    writer = SummaryWriter(f"runs/{run_name}")
    client = LoadMonitorClient()

    rl_agent = Agent(client.get_stats_size(),
                     client.get_action_size(), writer=writer)

    def check_valid():
        return None, client.valid()

    get_handler = {
        "/healthy": check_valid
    }

    def predict(raw_data):
        label = raw_data["pod_label"]
        pod_name = raw_data["pod_name"]
        nodes = raw_data["nodes"]
        result = dict()
        msg = ""
        result["node"] = nodes[0]
        result["pod"] = pod_name

        # print(nodes)
        # print(label)
        # print(pod_name)
        return result, True, msg

    def update(raw_data):
        pass

    post_handler = {
        "/predict": predict,
        "/update": update
    }

    class RequestHandlerImpl(http.server.BaseHTTPRequestHandler):

        def do_GET(self):
            path = re.sub("/+", "/", self.path)
            if path not in get_handler:
                self.send_error(404, self.path, ' not found')
                return

            result, vaild = get_handler[path]()
            if vaild:
                self.send_response(200)
            else:
                self.send_response(500)

            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()

            if result != None:
                self.wfile.write(result.encode("utf-8"))

        def do_POST(self):
            path = re.sub("/+", "/", self.path)

            if path not in post_handler:
                self.send_error(404, self.path, ' not found')
                return
            req_body = self.rfile.read(
                int(self.headers["Content-Length"])).decode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()

            resp = dict()

            try:
                json_data = json.loads(req_body)
                res, valid, msg = post_handler[path](json_data)

                if valid:
                    resp["state"] = "success"
                    resp["result"] = res
                else:
                    resp["state"] = "fail"

                resp["message"] = msg
                self.wfile.write(
                    json.dumps(resp).encode("utf-8"))
            except json.JSONDecodeError:
                resp["state"] = "fail"
                resp["message"] = "only support for json"
                self.wfile.write(
                    json.dumps(resp).encode("utf-8"))
                # print(req_body)

    server_address = (ADDRESS, PORT)
    httpd = http.server.HTTPServer(server_address, RequestHandlerImpl)
    logging.info("starting http server")
    httpd.serve_forever()


if __name__ == '__main__':
    run()
