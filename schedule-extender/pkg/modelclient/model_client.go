package modelclient

import (
	"context"
	"fmt"
	"log"
	"sync"
	"sync/atomic"
	"time"
	"unsafe"

	pb "github.com/charstal/schedule-extender/pbs"
	"github.com/charstal/schedule-extender/pkg/utils"
	"google.golang.org/grpc"
)

type CpuUnit float64
type MemoryUnit float64

type Resource struct {
	Cpu    CpuUnit
	Memory MemoryUnit
}

type ModelClient struct {
	client pb.ModelPredictClient
	mu     sync.RWMutex
}

const (
	address = "localhost:50051"
)

var (
	globalClientConn unsafe.Pointer
	lck              sync.Mutex
)

func (mc *ModelClient) Predict(usage Resource, rules string, podName string) string {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	r, err := mc.client.Predict(ctx, &pb.Usage{
		CpuUsage:     float64(usage.Cpu),
		MemeoryUsage: float64(usage.Memory),
		OtherRules:   rules,
		PodName:      podName,
	})
	if err != nil {
		utils.LogWrite(utils.LOG_FATAL, fmt.Sprintf("could not greet: %v", err))
		log.Fatalf("could not greet: %v", err)
	}
	utils.LogWrite(utils.LOG_INFO, fmt.Sprintf("The selected node %s", r.GetNodeName()))
	log.Printf("The selected node %s", r.GetNodeName())
	return r.GetNodeName()
}

func GetClient() (*ModelClient, error) {
	conn, err := GetConn()
	if err != nil {
		return nil, err
	}
	mc := &ModelClient{
		client: pb.NewModelPredictClient(conn),
	}
	return mc, nil
}

func GetConn() (*grpc.ClientConn, error) {
	if atomic.LoadPointer(&globalClientConn) != nil {
		return (*grpc.ClientConn)(globalClientConn), nil
	}
	lck.Lock()
	defer lck.Unlock()
	if atomic.LoadPointer(&globalClientConn) != nil {
		return (*grpc.ClientConn)(globalClientConn), nil
	}
	cli, err := newGRPCConn()
	if err != nil {
		return nil, err
	}
	atomic.StorePointer(&globalClientConn, unsafe.Pointer(cli))
	return cli, nil
}

func newGRPCConn() (*grpc.ClientConn, error) {
	conn, err := grpc.Dial(
		address,
		grpc.WithInsecure(),
	)
	if err != nil {
		return nil, err
	}
	return conn, nil
}

// func (mc *ModelClient) ReConnect() {
// 	mc.client
// }

func main() {
	client, _ := GetClient()
	println(client.Predict(Resource{
		Cpu:    0.4,
		Memory: 0.5,
	}, "", "hello"))

}
