package config

var (
	// Default 1 core CPU usage for containers without requests and limits i.e. Best Effort QoS.
	DefaultRequestsMilliCores  int64 = 1000
	DefaultRequestsMilliMemory int64 = 1000
	// Default requests multiplier for containers without limits predicted as 1.5*requests i.e. Burstable QoS class
	DefaultRequestsMultiplier = "1"
)
