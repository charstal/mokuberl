FROM golang:1.17

COPY . /schedule-extender
WORKDIR /schedule-extender
RUN go env -w GO111MODULE=on
RUN go env -w GOPROXY=https://goproxy.cn,direct

RUN make build


FROM alpine:3.12

COPY --from=0 /schedule-extender/_output/schedule-extender /bin/schedule-extender

WORKDIR /bin
CMD ["schedule-extender"]