from gym.spaces import Discrete, Box
import numpy as np
import warnings
import magent
from pettingzoo import AECEnv
import math
from pettingzoo.magent.render import Renderer
from pettingzoo.utils import agent_selector
from .magent_env import magent_parallel_env, make_env
from pettingzoo.utils._parallel_env import _parallel_env_wrapper
from pettingzoo.utils.to_parallel import parallel_wrapper_fn
from gym.utils import EzPickle


map_size = 45
max_frames_default = 500
minimap_mode = False
default_reward_args = dict(attack_penalty=-0.2)


def parallel_env(max_frames=max_frames_default, **reward_args):
    env_reward_args = dict(**default_reward_args)
    env_reward_args.update(reward_args)
    return _parallel_env(map_size, env_reward_args, max_frames)


def raw_env(max_frames=max_frames_default, **reward_args):
    return _parallel_env_wrapper(parallel_env(max_frames, **reward_args))


env = make_env(raw_env)


def get_config(map_size, attack_penalty):
    gw = magent.gridworld
    cfg = gw.Config()

    cfg.set({"map_width": map_size, "map_height": map_size})
    cfg.set({"minimap_mode": minimap_mode})

    options = {
        'width': 2, 'length': 2, 'hp': 1, 'speed': 1,
        'view_range': gw.CircleRange(5), 'attack_range': gw.CircleRange(2),
        'attack_penalty': attack_penalty
    }
    predator = cfg.register_agent_type(
        "predator",
        options
    )

    options = {
        'width': 1, 'length': 1, 'hp': 1, 'speed': 1.5,
        'view_range': gw.CircleRange(4), 'attack_range': gw.CircleRange(0)
    }
    prey = cfg.register_agent_type(
        "prey",
        options
    )

    predator_group = cfg.add_group(predator)
    prey_group = cfg.add_group(prey)

    a = gw.AgentSymbol(predator_group, index='any')
    b = gw.AgentSymbol(prey_group, index='any')

    cfg.add_reward_rule(gw.Event(a, 'attack', b), receiver=[a, b], value=[1, -1])

    return cfg


class _parallel_env(magent_parallel_env, EzPickle):
    def __init__(self, map_size, reward_args, max_frames):
        EzPickle.__init__(self, map_size, reward_args, max_frames)
        env = magent.GridWorld(get_config(map_size, **reward_args), map_size=map_size)

        handles = env.get_handles()
        reward_vals = np.array([1, -1] + list(reward_args.values()))
        reward_range = [np.minimum(reward_vals, 0).sum(), np.maximum(reward_vals, 0).sum()]

        names = ["predator", "prey"]
        super().__init__(env, handles, names, map_size, max_frames, reward_range, minimap_mode)

    def generate_map(self):
        env, map_size = self.env, self.map_size
        handles = env.get_handles()

        env.add_walls(method="random", n=map_size * map_size * 0.03)
        env.add_agents(handles[0], method="random", n=map_size * map_size * 0.0125)
        env.add_agents(handles[1], method="random", n=map_size * map_size * 0.025)
