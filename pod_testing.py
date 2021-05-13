from kubernetes import client, config, utils
from kubernetes.client.api.apps_v1_api import AppsV1Api
import yaml
from os import path
import threading
import time

config.load_kube_config()

ONLY_CPU_FILE = path.join(path.dirname(
    __file__), "deploy", "cpu-test-deploy.yaml")

ONLY_MEMORY_FILE = path.join(path.dirname(
    __file__), "deploy", "memory-test-deploy.yaml")

BALANCED_FILE = path.join(path.dirname(
    __file__), "deploy", "balanced-test-deploy.yaml")

k8s_app_v1 = client.AppsV1Api()
k8s_api_client = client.ApiClient()
# ONLG_CPU_YAML = yaml.safe_load(ONLY_CPU_FILE)
# ONLG_MEMORY_YAML = yaml.safe_load(ONLY_MEMORY_FILE)
# BALANCED_YAML = yaml.safe_load(BALANCED_FILE)


def only_cpu():
    while True:
        resp = utils.create_from_yaml(
            k8s_api_client, ONLY_CPU_FILE, namespace="default", verbose=True)

        time.sleep(200)
        resp = k8s_app_v1.delete_namespaced_deployment(
            name="cpu-test-deploy", namespace="default")

        print("cpu deployment delete. status='%s'" % resp)
        time.sleep(10)


def only_memory():
    while True:
        resp = utils.create_from_yaml(
            k8s_api_client, ONLY_MEMORY_FILE, namespace="default", verbose=True)

        time.sleep(200)
        resp = k8s_app_v1.delete_namespaced_deployment(
            name="memory-test-deploy", namespace="default")

        print("memory deployment delete. status='%s'" % resp)
        time.sleep(10)


def blanced():
    while True:
        resp = utils.create_from_yaml(
            k8s_api_client, BALANCED_FILE, namespace="default", verbose=True)

        time.sleep(200)
        resp = k8s_app_v1.delete_namespaced_deployment(
            name="balanced-test-deploy", namespace="default")

        print("blanced deployment delete. status='%s'" % resp)
        time.sleep(10)


def main():
    threading.Thread(target=only_cpu).start()
    threading.Thread(target=only_memory).start()
    threading.Thread(target=blanced).start()


if __name__ == "__main__":
    main()
