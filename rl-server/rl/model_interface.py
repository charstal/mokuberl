from collections import deque
import numpy as np
import torch
import time
import sched
from threading import Lock, Thread

from .schedule_env import ScheduleEnv
from .dqn_agent import Agent
from config import ModelConfig
from utils import Cache
from pbs import ModelPredictServicer, model_predict_pb2
from client import Resource

cache = Cache()
cache_lock = Lock()
train_lock = Lock()
s = sched.scheduler(time.time, time.sleep)
train_cnt = 0


EPS_START = ModelConfig.get_eps_start()
EPS_END = ModelConfig.get_eps_end()
EPS_DECAY = ModelConfig.get_eps_decay()
SAVE_MODEL_TRAIN_TIMES = ModelConfig.get_mode_save_train_times()
TRAIN_INTERVAL = ModelConfig.get_train_interval()
MODEL_SAVE_PATH = ModelConfig.get_model_path()


class ModelPredict(ModelPredictServicer):
    def __init__(self):

        self.env = ScheduleEnv()
        self.agent = Agent(
            state_size=self.env.get_state_size(),
            action_size=self.env.get_action_size(),
            seed=0)
        self.scores = deque(maxlen=100)

        # self.states = self.env.reset()
        self.eps = EPS_START

    def Predict(self, request, context):
        pod_name = request.podName
        print("starting predict:", pod_name, flush=True)

        cache_lock.acquire()
        node_name = cache.get(pod_name)
        cache_lock.release()

        # print("node name:", node_name)
        if node_name == None:
            cpuUsage = float(request.cpuUsage)
            memoryUsage = float(request.memeoryUsage)
            train_lock.acquire()
            states = self.env.get_states(
                Resource(cpu=cpuUsage, memory=memoryUsage))
            action = self.agent.act(state=states)
            node_name = self.env.pre_step(action)
            train_lock.release()

            cache_lock.acquire()
            cache.set(pod_name, node_name, 60)
            cache_lock.release()

            Thread(target=self.task, args=(action,)).start()

        return model_predict_pb2.Choice(nodeName=node_name)

    def task(self, action):
        s.enter(TRAIN_INTERVAL, 1, self.train, (action,))
        s.run()

    def train(self, action):
        train_lock.acquire()
        print("training:", flush=True)
        states = self.env.get_states()
        next_states, reward, done, _ = self.env.step(action, states)
        score = 0

        self.agent.step(state=states, action=action,
                        reward=reward, next_state=next_states, done=done)
        # print(states)
        # print(next_states)
        # self.states = next_states

        score += reward
        self.scores.append(score)
        self.eps = max(EPS_END, EPS_END*self.eps)  # decrease epsilon
        train_cnt += 1

        if self.cnt % SAVE_MODEL_TRAIN_TIMES == 0:
            torch.save(self.agent.qnetwork_local.state_dict(),
                       MODEL_SAVE_PATH)
            print("train times: {}".format(train_cnt), flush=True)

            # 上限 2w
            if train_cnt == 20000:
                train_cnt = 0
        # print("finished training")
        train_lock.release()

        print('\tAverage Score: {:.2f}\n'.format(
            np.mean(self.scores)), end="", flush=True)
