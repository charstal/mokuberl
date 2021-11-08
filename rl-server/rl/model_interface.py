from collections import deque
import numpy as np
import torch
import time
import sched
from threading import Lock, Thread
import multiprocessing as mp

from .schedule_env import ScheduleEnv
from .dqn_agent import Agent
from config import ModelConfig
from config import SysConfig
from utils import Cache
from pbs import ModelPredictServicer, model_predict_pb2
from client import Resource
from metrics import Monitor
from flow_control import FlowController

cache = Cache()
cache_lock = Lock()
train_lock = Lock()
s = sched.scheduler(time.time, time.sleep)
flow_controller = FlowController(
    capacity=SysConfig.get_flow_capacity(), rate=SysConfig.get_flow_rate())

EPS_START = ModelConfig.get_eps_start()
EPS_END = ModelConfig.get_eps_end()
EPS_DECAY = ModelConfig.get_eps_decay()
SAVE_MODEL_TRAIN_TIMES = ModelConfig.get_mode_save_train_times()
TRAIN_INTERVAL = ModelConfig.get_train_interval()
MODEL_SAVE_PATH = ModelConfig.get_model_path()

time_str = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
LOG_PATH = "metrics/data/log-{}.csv".format(time_str)
log_file = open(LOG_PATH, mode='w')


def start_monitor():
    m = Monitor()
    m.start()


mp.Process(target=start_monitor).start()


class ModelPredict(ModelPredictServicer):
    def __init__(self):

        self.start_time = time.time()
        self.env = ScheduleEnv()
        self.agent = Agent(
            state_size=self.env.get_state_size(),
            action_size=self.env.get_action_size(),
            seed=0)
        self.scores = deque(maxlen=2000)
        self.train_cnt = 0
        # self.states = self.env.reset()
        self.eps = EPS_START

    def Predict(self, request, context):
        pod_name = request.podName

        if not flow_controller.grant():
            return model_predict_pb2.Choice(nodeName="overrate")

        cache_lock.acquire()
        node_name = cache.get(pod_name)
        cache_lock.release()

        # print("node name:", node_name)
        if node_name == None:
            print("starting predict:", pod_name, flush=True)
            cache_lock.acquire()
            node_name = cache.get(pod_name)
            if node_name != None:
                cache_lock.release()
            else:
                cpuUsage = float(request.cpuUsage)
                memoryUsage = float(request.memeoryUsage)
                pod_resource = Resource(cpu=cpuUsage, memory=memoryUsage)

                train_lock.acquire()
                states = self.env.get_states(pod_resource=pod_resource)
                action = self.agent.act(state=states, eps=self.eps)
                node_name, transfer_action = self.env.pre_step(
                    action, pod_resource)
                train_lock.release()

                cache.set(pod_name, node_name, 60)
                cache_lock.release()

                # if action changed means that action from load packing
                if action == transfer_action:
                    Thread(target=self.task, args=(action, states)).start()
                else:
                    Thread(target=self.train, args=(
                        action, states, self.env.get_normal_negative_reward(), states, False)).start()

        node_name = self.env.check_overload(node_name)
        print(node_name)

        return model_predict_pb2.Choice(nodeName=node_name)

    def task(self, action, states):
        s.enter(TRAIN_INTERVAL, 1, self.env_trian, (action, states))
        s.run()

    def env_trian(self, action, states):
        # print("training:", flush=True)
        next_states, reward, done, _ = self.env.step(action)
        self.train(action, states, reward, next_states, done)

    def train(self, action, states, reward, next_states, done):
        train_lock.acquire()
        print("action: ", self.env.action2node(action))
        # print("current states: ", states)
        # print("next states: ", next_states)
        print("reward: ", reward)
        print("done: ", done)
        self.agent.step(state=states, action=action,
                        reward=reward, next_state=next_states, done=done)
        # print(states)
        # print(next_states)
        # self.states = next_states

        score = reward
        self.scores.append(score)
        self.eps = max(EPS_END, EPS_DECAY*self.eps)  # decrease epsilon
        self.train_cnt += 1

        if self.train_cnt % SAVE_MODEL_TRAIN_TIMES == 0:
            torch.save(self.agent.qnetwork_local.state_dict(),
                       MODEL_SAVE_PATH)
            # print("train times: {}".format(self.train_cnt), flush=True)

            # 上限 2w
            if self.train_cnt == 20000:
                self.train_cnt = 0
        # print("finished training")

        spend_time = int(time.time() - self.start_time)
        print("\ttime:\t", spend_time)
        print('\tAverage Score: {:.2f}\n'.format(
            np.mean(self.scores)), end="", flush=True)

        log_file.write(str(spend_time) + ",{},{:.2f}\n".format(self.train_cnt,
                                                               np.mean(self.scores)))
        log_file.flush()

        train_lock.release()
