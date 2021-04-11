from pbs import ModelPredictServicer, model_predict_pb2
from .schedule_env import ScheduleEnv
from k8s import Resource
from .dqn_agent import Agent
from collections import deque
from config import TRAIN_INTERVAL_SECONDS, MODEL_PATH
import numpy as np
import torch
import time
import sched
from threading import Lock, Thread
from utils import Cache

cache = Cache()

lock = Lock()

eps_start = 1.0
eps_end = 0.01
eps_decay = 0.995

s = sched.scheduler(time.time, time.sleep)


class ModelPredict(ModelPredictServicer):
    def __init__(self):
        self.env = ScheduleEnv()
        self.agent = Agent(state_size=self.env.get_state_size(
        ), action_size=self.env.get_action_size(), seed=0)
        self.states = self.env.reset()
        self.scores = deque(maxlen=100)
        self.eps = eps_start

    def Predict(self, request, context):
        podName = request.podName
        print("starting predict:", request.podName, flush=True)
        lock.acquire()
        node_name = cache.get(podName)
        lock.release()

        # print("node name:", node_name)
        if node_name != None:
            return model_predict_pb2.Choice(nodeName=node_name)

        lock.acquire()
        states = self.states
        action = self.agent.act(state=states)
        node_name = self.env.pre_step(action)
        cache.set(podName, node_name, 60)
        lock.release()

        Thread(target=self.task, args=(action,)).start()
        # mem cpu pod usage + rules: kind.

        return model_predict_pb2.Choice(nodeName=node_name)

    def task(self, action):
        s.enter(TRAIN_INTERVAL_SECONDS, 1, self.train, (action,))
        s.run()

    def train(self, action):
        print("training:")
        lock.acquire()
        states = self.states
        next_states, reward, done, _ = self.env.step(action, states)
        score = 0

        self.agent.step(state=states, action=action,
                        reward=reward, next_state=next_states, done=done)
        # print(states)
        # print(next_states)
        self.states = next_states

        score += reward
        self.scores.append(score)
        self.eps = max(eps_end, eps_decay*self.eps)  # decrease epsilon

        torch.save(self.agent.qnetwork_local.state_dict(), MODEL_PATH)
        # print("finished training")
        lock.release()

        print('\tAverage Score: {:.2f}\n'.format(
            np.mean(self.scores)), end="", flush=True)
