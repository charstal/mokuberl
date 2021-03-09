from concurrent import futures
import logging

import grpc

import pbs.model_predict_pb2 as model_predict_pb2
import pbs.model_predict_pb2_grpc as model_predict_pb2_grpc


class ModelPredict(model_predict_pb2_grpc.ModelPredictServicer):

    def Predict(self, request, context):
        return model_predict_pb2.ScoreResult(score=request.memeoryUsage+request.cpuUsage)


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
