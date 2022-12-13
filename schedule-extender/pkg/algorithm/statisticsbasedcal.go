package algorithm

import (
	"math"

	"github.com/charstal/schedule-extender/pkg/resourcestats"
	"k8s.io/klog/v2"
	"k8s.io/kubernetes/pkg/scheduler/framework"
)

/*
Calculation of risk score for resources given measured data
*/

// computeScore : compute score given usage statistics
// - risk = [ average + margin * stDev^{1/sensitivity} ] / 2
// - score = ( 1 - risk ) * maxScore
func ComputeScore(rs *resourcestats.ResourceStats, margin float64, sensitivity float64) float64 {
	if rs.Capacity <= 0 {
		klog.ErrorS(nil, "Invalid resource capacity", "capacity", rs.Capacity)
		return 0
	}

	// make sure values are within bounds
	rs.Req = math.Max(rs.Req, 0)
	rs.UsedAvg = math.Max(math.Min(rs.UsedAvg, rs.Capacity), 0)
	rs.UsedStdev = math.Max(math.Min(rs.UsedStdev, rs.Capacity), 0)

	// calculate average and deviation factors
	mu, sigma := resourcestats.GetMuSigma(rs)

	// apply root power
	if sensitivity >= 0 {
		sigma = math.Pow(sigma, 1/sensitivity)
	}
	// apply multiplier
	sigma *= margin
	sigma = math.Max(math.Min(sigma, 1), 0)

	// evaluate overall risk factor
	risk := (mu + sigma) / 2
	klog.V(6).InfoS("Evaluating risk factor", "mu", mu, "sigma", sigma, "margin",
		margin, "sensitivity", sensitivity, "risk", risk)
	return (1. - risk) * float64(framework.MaxNodeScore)
}
