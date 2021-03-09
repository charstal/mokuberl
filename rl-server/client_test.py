from __future__ import print_function
import logging

import grpc

import pbs.model_predict_pb2 as model_predict_pb2
import pbs.model_predict_pb2_grpc as model_predict_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    node_name = 'node-worker1'
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = model_predict_pb2_grpc.ModelPredictStub(channel)
        response = stub.Predict(model_predict_pb2.Usage(
            cpuUsage=0.3,
            memeoryUsage=0.4,
            otherRules='',
            nodeName=node_name
        ))
    print(node_name + " score: " + str(response.score))


if __name__ == '__main__':
    logging.basicConfig()
    run()
