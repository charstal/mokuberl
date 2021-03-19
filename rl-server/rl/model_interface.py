import pbs.model_predict_pb2 as model_predict_pb2
import pbs.model_predict_pb2_grpc as model_predict_pb2_grpc

class ModelPredict(model_predict_pb2_grpc.ModelPredictServicer):
    def Predict(self, request, context):
        return model_predict_pb2.ScoreResult(score=request.memeoryUsage+request.cpuUsage)
