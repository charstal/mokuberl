#!/bin/bash
source /home/charstal/.virtualenvs/k8s/bin/activate
python -m grpc_tools.protoc -I./protos --python_out=./pbs --grpc_python_out=./pbs ./protos/model_predict.proto
deactivate