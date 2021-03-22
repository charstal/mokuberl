package main

import (
	"context"
	"log"
	"os"
	"sync"
	"time"

	pb "github.com/charstal/schedule-extender/pbs"
	"google.golang.org/grpc"
)

const (
	address     = "localhost:50051"
	defaultName = "world"
)

type ModelClient struct {
	client grpc.ClientConn
	mu     sync.RWMutex
}

func main() {
	// Set up a connection to the server.
	conn, err := grpc.Dial(address, grpc.WithInsecure(), grpc.WithBlock())
	if err != nil {
		log.Fatalf("did not connect: %v", err)
	}
	defer conn.Close()
	c := pb.NewModelPredictClient(conn)

	// Contact the server and print out its response.
	nodeName := defaultName
	if len(os.Args) > 1 {
		nodeName = os.Args[1]
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	r, err := c.Predict(ctx, &pb.Usage{
		CpuUsage:     0.3,
		MemeoryUsage: 0.4,
		OtherRules:   "",
		NodeName:     nodeName,
	})
	if err != nil {
		log.Fatalf("could not greet: %v", err)
	}
	log.Printf("%s  score: %f", nodeName, r.GetScore())
}
