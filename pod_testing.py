from kubernetes import client, config, utils
from kubernetes.client import BatchV1Api
import yaml
from os import path
import threading
import time
import sched
import copy


s = sched.scheduler(time.time, time.sleep)

config.load_kube_config()

k8s_app_client = BatchV1Api()
apps_v1 = client.AppsV1Api()

RANDOM_LOAD_FILE_PATH = path.join(path.dirname(
    __file__), "deploy", "random-load-job.yaml")
RANDOM_LOAD_FILE = open(RANDOM_LOAD_FILE_PATH)
RANDOM_LOAD_YAML = yaml.safe_load(RANDOM_LOAD_FILE)


NODE_RESOURCE_BALANCED_ALLOCATION_FILE_PATH = path.join(path.dirname(
    __file__), "deploy", "baseline", "node-resource-balanced-allocation-job.yaml")
NODE_RESOURCE_BALANCED_ALLOCATION_FILE = open(
    NODE_RESOURCE_BALANCED_ALLOCATION_FILE_PATH)
NODE_RESOURCE_BALANCED_ALLOCATION_YAML = yaml.safe_load(
    NODE_RESOURCE_BALANCED_ALLOCATION_FILE)


NODE_RESOURCE_LEAST_ALLOCATED_FILE_PATH = path.join(path.dirname(
    __file__), "deploy", "baseline", "node-resource-least-allocated-job.yaml")
NODE_RESOURCE_LEAST_ALLOCATED_FILE = open(
    NODE_RESOURCE_LEAST_ALLOCATED_FILE_PATH)
NODE_RESOURCE_LEAST_ALLOCATED_YAML = yaml.safe_load(
    NODE_RESOURCE_LEAST_ALLOCATED_FILE)


POD_TOPOLOG_SPREAD_FILE_PATH = path.join(path.dirname(
    __file__), "deploy", "baseline", "pod-topolog-spread-job.yaml")
POD_TOPOLOG_SPREAD_FILE = open(POD_TOPOLOG_SPREAD_FILE_PATH)
POD_TOPOLOG_SPREAD_YAML = yaml.safe_load(POD_TOPOLOG_SPREAD_FILE)


SELECTOR_SPREAD_FILE_PATH = path.join(path.dirname(
    __file__), "deploy", "baseline", "selector-spread-job.yaml")
SELECTOR_SPREAD_FILE = open(SELECTOR_SPREAD_FILE_PATH)
SELECTOR_SPREAD_YAML = yaml.safe_load(SELECTOR_SPREAD_FILE)


TARGET_LOAD_PACKING_FILE_PATH = path.join(path.dirname(
    __file__), "deploy", "baseline", "target-load-packing-job.yaml")
TARGET_LOAD_PACKING_FILE = open(TARGET_LOAD_PACKING_FILE_PATH)
TARGET_LOAD_PACKING_YAML = yaml.safe_load(TARGET_LOAD_PACKING_FILE)


RANDOM_LOAD_FILE.close()
NODE_RESOURCE_BALANCED_ALLOCATION_FILE.close()
NODE_RESOURCE_LEAST_ALLOCATED_FILE.close()
POD_TOPOLOG_SPREAD_FILE.close()
SELECTOR_SPREAD_FILE.close()
TARGET_LOAD_PACKING_FILE.close()


yaml_list = [RANDOM_LOAD_YAML, NODE_RESOURCE_BALANCED_ALLOCATION_YAML,
             NODE_RESOURCE_LEAST_ALLOCATED_YAML, POD_TOPOLOG_SPREAD_YAML, SELECTOR_SPREAD_YAML, TARGET_LOAD_PACKING_YAML]


def stress_load():

    k8s_app_client.delete_collection_namespaced_job(
        namespace="default", propagation_policy='Background')
    time.sleep(10)
    cnt = 0
    while True:
        dep = copy.deepcopy(yaml_list[1])
        dep["metadata"]["name"] = dep["metadata"]["name"] + "-" + str(cnt)
        k8s_app_client.create_namespaced_job(
            body=dep, namespace="default")

        # s.enter(80, 1, delete_job, (dep))
        cnt += 1
        print("epoch:", cnt)
        time.sleep(5)


def delete_job(dep):
    resp = k8s_app_client.delete_namespaced_job(
        name=dep["metadata"]["name"], namespace="default", propagation_policy='Background')


def main():
    threading.Thread(target=stress_load).start()
    # threading.Thread(target=only_memory).start()
    # threading.Thread(target=blanced).start()


if __name__ == "__main__":
    main()
