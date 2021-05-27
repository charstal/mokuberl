from kubernetes import client, config, utils
import kubernetes
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
RANDOM_LOAD_FILE.close()

# ONLY_MEMORY_FILE = path.join(path.dirname(
#     __file__), "deploy", "memory-test-deploy.yaml")

# BALANCED_FILE = path.join(path.dirname(
#     __file__), "deploy", "balanced-test-deploy.yaml")


# ONLG_MEMORY_YAML = yaml.safe_load(ONLY_MEMORY_FILE)
# BALANCED_YAML = yaml.safe_load(BALANCED_FILE)


def stress_load():

    k8s_app_client.delete_collection_namespaced_job(
        namespace="default", propagation_policy='Background')

    cnt = 0
    while True:
        dep = copy.deepcopy(RANDOM_LOAD_YAML)
        dep["metadata"]["name"] = dep["metadata"]["name"] + "-" + str(cnt)
        k8s_app_client.create_namespaced_job(
            body=dep, namespace="default")

        s.enter(200, 1, delete_job, (dep))
        cnt += 1
        print("epoch:", cnt)
        time.sleep(70)


def delete_job(dep):
    resp = k8s_app_client.delete_namespaced_job(
        name=dep["metadata"]["name"], namespace="default", propagation_policy='Background')

    # def only_memory():
    #     while True:
    #         resp = utils.create_from_yaml(
    #             k8s_api_client, ONLY_MEMORY_FILE, namespace="default", verbose=True)

    #         time.sleep(200)
    #         resp = k8s_app_v1.delete_namespaced_deployment(
    #             name="memory-test-deploy", namespace="default")

    #         print("memory deployment delete. status='%s'" % resp)
    #         time.sleep(10)

    # def blanced():
    #     while True:
    #         resp = utils.create_from_yaml(
    #             k8s_api_client, BALANCED_FILE, namespace="default", verbose=True)

    #         time.sleep(200)
    #         resp = k8s_app_v1.delete_namespaced_deployment(
    #             name="balanced-test-deploy", namespace="default")

    #         print("blanced deployment delete. status='%s'" % resp)
    #         time.sleep(10)


def main():
    threading.Thread(target=stress_load).start()
    # threading.Thread(target=only_memory).start()
    # threading.Thread(target=blanced).start()


if __name__ == "__main__":
    main()
