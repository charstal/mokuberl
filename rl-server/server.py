from concurrent import futures
import logging

import grpc

import os
from config import SysConfig
from pbs import model_predict_pb2_grpc
from rl import ModelPredict

PORT = SysConfig.get_grpc_port()


def serve():
    print("start server........", flush=True)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_predict_pb2_grpc.add_ModelPredictServicer_to_server(
        ModelPredict(), server)

    server.add_insecure_port('[::]:' + PORT)
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
