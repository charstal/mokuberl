#!/bin/bash
source /home/charstal/.virtualenvs/k8s/bin/activate
python -m grpc_tools.protoc -I./grpc/protos --python_out=./grpc --grpc_python_out=./grpc ./grpc/protos/model_predict.proto
deactivate