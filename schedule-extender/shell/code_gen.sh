#!/bin/bash
protoc --go_out=.  \
    --go-grpc_out=.  \
    protos/model_predict.proto