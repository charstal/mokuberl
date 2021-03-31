# node resource class
# C: cpu
# M: memory
NODE_CLASS = ["C", "M"]

NODE_CLASS_CPU = "C"
NODE_CLASS_MEMORY = "M"

# node state
# 1, can be scheduled
# 0, cannot be scheduled
NODE_STATE = [0, 1]

# node amount
DEFAULT_NODE_SIZE = 10

CLASS_THRESHOLD = {
    NODE_CLASS_CPU: 70,
    NODE_CLASS_MEMORY: 70
}
NODE_CPU_THRESHOLD = 70
NODE_MEMORY_THRESHOLD = 70