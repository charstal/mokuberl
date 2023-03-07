from kubernetes import client, config
import yaml
import time

s = """apiVersion: v1
kind: Pod
metadata:
  name: random-load-pod-{kind}-{num}
  labels:
    course_id: {kind}
spec:
  schedulerName: {scheduler}
  containers:
    - name: random-load
      image: registry.cn-shanghai.aliyuncs.com/charstal/random_load
      imagePullPolicy: Always
      resources:
        requests:
          cpu: 20m
          memory: 20Mi
        limits:
          cpu: 4
          memory: 4000Mi
      volumeMounts:
        - name: config-volume
          mountPath: /etc/random-load
  volumes:
    - name: config-volume
      configMap:
        name: random-load-config-{kind}
  restartPolicy: Never"""


config.load_kube_config()
k8s_app_client = client.CoreV1Api()


def get_yaml(kind, num, scheduler):
    ss = s.format(kind=kind, num=num, scheduler=scheduler)
    return yaml.safe_load(ss)


def excute(yaml_src):
    k8s_app_client.create_namespaced_pod(
        body=yaml_src, namespace="default")


def run():
    scheduler = "SchedulerPluginAgent"
    kind_list = ["a"]
    kind_dict = {"a": 0, "b": 0, "c": 0, "d": 0}
    cnt = 0
    while True:
        for k in kind_list:
            num = kind_dict[k]
            kind_dict[k] += 1
            yaml_src = get_yaml(k, num, scheduler)
            cnt += 1
            excute(yaml_src)
            print(cnt)
            time.sleep(15)


if __name__ == "__main__":
    run()
