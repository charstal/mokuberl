from concurrent import futures
import logging

import grpc

import os
from config import PORT
from pbs import model_predict_pb2_grpc
from rl import ModelPredict


def serve():
    print("start server........", flush=True)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_predict_pb2_grpc.add_ModelPredictServicer_to_server(
        ModelPredict(), server)
    port = os.getenv('path')
    if port == None:
        port = PORT
    server.add_insecure_port('[::]:' + port)
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
