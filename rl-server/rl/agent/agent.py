import random
import os
import time
from collections import deque, namedtuple


import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim

from config import ModelConfig
from model import QNetWork


# BUFFER_SIZE = int(1e5)  # replay buffer size
# BATCH_SIZE = 64         # minibatch size
# GAMMA = 0.99            # discount factor
# TAU = 1e-3              # for soft update of target parameters
# LR = 5e-4               # learning rate
# UPDATE_EVERY = 4        # how often to update the network

# BUFFER_SIZE = ModelConfig.get_buffer_size()
# BATCH_SIZE = ModelConfig.get_batch_size()
# GAMMA = ModelConfig.get_gamma()
# TAU = ModelConfig.get_tau()
# LR = ModelConfig.get_lr()
# UPDATE_EVERY = ModelConfig.get_update_every()
# MODEL_PATH = ModelConfig.get_model_path()

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class Agent():
    def __init__(
        self,
        state_size,
        action_size,
        learning_rate=2.5e-4,
        tau=0.5,
        gamma=0.99,
        start_e=1,
        end_e=0.05,
        epsilon_decay=0.995,
        exploration_fration=0.5,
        learning_start=10000,
        replace_target_iter=500,
        train_frequnecy=10,
        buffer_size=int(1e5),
        batch_size=128,
        model_path=None,
        writer=None,
        seed=1
    ):
        # state size
        self.state_size = state_size
        self.action_size = action_size
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.lr = learning_rate
        self.learning_start = learning_start
        self.tau = tau
        self.gamma = gamma
        # self.epsilon = start_e
        self.start_e = start_e
        self.end_e = end_e
        self.exploration_fraction = exploration_fration
        self.epsilon_deacy = epsilon_decay
        self.start_time = time.time()
        self.train_frequency = train_frequnecy
        self.replace_target_iter = replace_target_iter
        self.writer = writer
        self.model_path = model_path

        # total learning step
        self.global_step = 0
        self.total_step = 500000

        # memory buffer
        self.memory = ReplayBuffer(
            self.action_size, self.buffer_size, self.batch_size)

        # qnetwork
        self.qnetwork_local = QNetWork(
            state_size, action_size, seed).to(device)
        self.optimizer = optim.Adam(
            self.qnetwork_local.parameters(), lr=self.lr)
        self.qnetwork_target = QNetWork(
            state_size, action_size, seed).to(device)
        self.qnetwork_target.load_state_dict(self.qnetwork_local.state_dict())

        if model_path is not None and os.path.exists(model_path):
            self.qnetwork_local.load_state_dict(torch.load(model_path))
            self.qnetwork_target.load_state_dict(torch.load(model_path))

    def linear_schedule(self):
        duration = self.exploration_fraction * self.total_step
        slope = (self.end_e - self.start_e) / duration
        return max(slope * self.global_step + self.start_e, self.end_e)

    def step(self, state, action, reward, next_state, done):
        # save experienct in replay memory
        self.memory.add(state, action, reward, next_state, done)

        self.global_step += 1
        if self.global_step < self.learning_start:
            return

        if self.global_step % self.train_frequency == 0:
            exs = self.memory.sample()
            self.learn(exs, self.gamma)

    def act(self, state):
        """Returns actions for given state as per current policy.

        Params
        ======
            state (array_like): current state
            eps (float): epsilon, for epsilon-greedy action selection
        """

        # Epsilon-greedy action selection
        epsilon = self.linear_schedule()
        if random.random() > epsilon:
            state = torch.from_numpy(state).float().unsqueeze(0).to(device)
            self.qnetwork_local.eval()
            with torch.no_grad():
                action_values = self.qnetwork_local(state)
            self.qnetwork_local.train()
            action = np.argmax(action_values.cpu().data.numpy())
        else:
            action = np.random.randint(0, self.action_size)
        # print(action)
        return action

    def learn(self, experiences, gamma):
        """Update value parameters using given batch of experience tuples.
        Params
        ======
            experiences (Tuple[torch.Tensor]): tuple of (s, a, r, s', done) tuples 
            gamma (float): discount factor
        """
        states, actions, rewards, next_states, dones = experiences

        # Get max predicted Q values (for next states) from target model
        Q_targets_next = self.qnetwork_target(
            next_states).detach().max(1)[0].unsqueeze(1)
        # Compute Q targets for current states
        Q_targets = rewards + (gamma * Q_targets_next * (1 - dones))

        # Get expected Q values from local model
        Q_expected = self.qnetwork_local(states).gather(1, actions)

        # Compute loss
        loss = F.mse_loss(Q_expected, Q_targets)

        if self.global_step % 100 == 0:
            self.writer.add_scalar("losses/td_loss", loss, self.global_step)
            self.writer.add_scalar("losses/q_values",
                                   Q_targets.mean().item(), self.global_step)
            print("SPS:", int(self.global_step / (time.time() - self.start_time)))
            self.writer.add_scalar("charts/SPS", int(self.global_step /
                                                     (time.time() - self.start_time)), self.global_step)

        # Minimize the loss
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # ------------------- update target network ------------------- #
        if self.global_step % self.replace_target_iter == 0:
            self.soft_update(self.qnetwork_local,
                             self.qnetwork_target, self.tau)
            # self.epsilon = max(self.end_e, self.epsilon * self.epsilon_deacy)

    def soft_update(self, local_model, target_model, tau):
        """Soft update model parameters.
        θ_target = τ*θ_local + (1 - τ)*θ_target
        Params
        ======
            local_model (PyTorch model): weights will be copied from
            target_model (PyTorch model): weights will be copied to
            tau (float): interpolation parameter 
        """
        # for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
        #     target_param.data.copy_(
        #         tau*local_param.data + (1.0-tau)*target_param.data)
        target_model.load_state_dict(local_model.state_dict())


class ReplayBuffer:
    def __init__(self, action_size, buffer_size, batch_size):
        self.action_size = action_size
        self.memory = deque(maxlen=buffer_size)
        self.batch_size = batch_size
        self.experience = namedtuple("Experience", field_names=[
            "state", "action", "reward", "next_state", "done"
        ])

    def add(self, state, action, reward, next_state, done):
        """Add a experience to memory"""
        ex = self.experience(state, action, reward, next_state, done)
        self.memory.append(ex)

    def sample(self):
        """sample a batch from memory"""
        exs = random.sample(self.memory, k=self.batch_size)

        states = torch.from_numpy(
            np.vstack([e.state for e in exs if e is not None])).float().to(device)
        actions = torch.from_numpy(
            np.vstack([e.action for e in exs if e is not None])).long().to(device)
        rewards = torch.from_numpy(
            np.vstack([e.reward for e in exs if e is not None])).float().to(device)
        next_states = torch.from_numpy(np.vstack(
            [e.next_state for e in exs if e is not None])).float().to(device)
        dones = torch.from_numpy(np.vstack(
            [e.done for e in exs if e is not None]).astype(np.uint8)).float().to(device)

        return (states, actions, rewards, next_states, dones)

    def __len__(self):
        return len(self.memory)
