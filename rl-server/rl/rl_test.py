import time

import gym
from gym import Env
import numpy as np

from agent import Agent

from torch.utils.tensorboard import SummaryWriter


def run(env: Env, agent: Agent, writer: SummaryWriter):
    # initial observation
    observation, info = env.reset(seed=1)
    for episode in range(500000):

        # fresh env
        # env.render()
        # RL choose action based on observation
        action = agent.act(observation)

        # RL take action and get next observation and reward
        observation_, reward, terminated, truncated, info = env.step(action)
        # print(observation)

        if "episode" in info.keys():
            # print(
            #     f"global_step={episode}, episodic_return={info['episode']['r']}")
            writer.add_scalar("charts/reward",
                              info["episode"]["r"], episode)
            writer.add_scalar("charts/episodic_length",
                              info["episode"]["l"], episode)
            writer.add_scalar("charts/epsilon",
                              agent.linear_schedule(), episode)

        agent.step(observation, action, reward, observation_, terminated)

        # swap observation
        observation = observation_

        if terminated or truncated:
            observation, info = env.reset(seed=1)

    # end of game
    print('game over')
    # env.destroy()


if __name__ == "__main__":

    run_name = f"CartPole-v1_{int(time.time())}"
    writer = SummaryWriter(f"runs/{run_name}")

    env = gym.make("CartPole-v1")

    env = gym.wrappers.RecordEpisodeStatistics(env)
    # env.seed(seed)
    # env.action_space.seed(seed)
    # env.observation_space.seed(seed)
    # envs = gym.vector.SyncVectorEnv(
    #     [make_env("CartPole-v1", 1, 0, False, "test")])
    # assert isinstance(envs.single_action_space,
    #                   gym.spaces.Discrete), "only discrete action space is supported"
    agent = Agent(np.array(env.observation_space.shape).prod(),
                  env.action_space.n, writer=writer)
    run(env, agent, writer)

    writer.close()
    env.close()
