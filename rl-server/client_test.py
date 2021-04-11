from __future__ import print_function
import logging

import grpc

from pbs import model_predict_pb2, model_predict_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    podName = 'abcd'
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = model_predict_pb2_grpc.ModelPredictStub(channel)
        response = stub.Predict(model_predict_pb2.Usage(
            cpuUsage=0.3,
            memeoryUsage=0.4,
            otherRules='',
            podName=podName
        ))
    print(podName + " nodeName: " + str(response.nodeName))


if __name__ == '__main__':
    logging.basicConfig()
    run()
