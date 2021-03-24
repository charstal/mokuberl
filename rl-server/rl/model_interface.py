from pbs import ModelPredictServicer, model_predict_pb2

class ModelPredict(ModelPredictServicer):
    def Predict(self, request, context):
        return model_predict_pb2.Choice(nodeName="test")
