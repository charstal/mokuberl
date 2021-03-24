from concurrent import futures
import logging

import grpc

from pbs import model_predict_pb2_grpc
from rl import ModelPredict



def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_predict_pb2_grpc.add_ModelPredictServicer_to_server(
        ModelPredict(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
