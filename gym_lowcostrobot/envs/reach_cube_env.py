import time

import mujoco
import mujoco.viewer
import numpy as np
from gymnasium import spaces

from gym_lowcostrobot.envs.base_env import BaseRobotEnv


class ReachCubeEnv(BaseRobotEnv):
    def __init__(self, image_state=False, action_mode="joint", render_mode=None):
        super().__init__(
            xml_path="assets/scene_one_cube.xml",
            image_state=image_state,
            action_mode=action_mode,
            render_mode=render_mode,
        )

        # Define the action space and observation space
        if self.action_mode == "ee":
            self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        else:
            self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(5,), dtype=np.float32)
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self.data.xpos.flatten().shape[0] + 3,),
            dtype=np.float32,
        )

        # Initialize the robot and target positions
        self.threshold_distance = 0.01

        self.object_low = np.array([0.0, 0.0, 0.01])
        self.object_high = np.array([0.2, 0.2, 0.01])

    def reset(self, seed=None, options=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed, options=options)

        # Sample and set the object position
        self.data.joint("red_box_joint").qpos[:3] = self.np_random.uniform(self.object_low, self.object_high)

        # Step the simulation
        mujoco.mj_step(self.model, self.data)
        self.step_start = time.time()

        # Get the additional info
        info = self.get_info()

        return self.get_observation(), info

    def get_observation(self):
        box_id = self.model.body("box").id
        return np.concatenate([self.data.xpos.flatten(), self.data.xpos[box_id]], dtype=np.float32)

    def step(self, action):
        # Perform the action and step the simulation
        self.base_step_action_nograsp(action)

        # Get the new observation
        observation = self.get_observation()

        # cube_id = self.model.body("box").id
        # cube_pos = self.data.geom_xpos[cube_id]
        cube_pos = self.data.joint("red_box_joint").qpos[:3]
        # ee_id = self.model.body("joint5-pad").id
        # ee_pos = self.data.geom_xpos[ee_id]
        ee_pos = self.data.joint("joint5").qpos[:3]
        distance = np.linalg.norm(cube_pos - ee_pos)

        # Compute the reward based on the distance
        reward = -distance

        # The episode is terminated if the distance is less than the threshold
        terminated = distance < self.threshold_distance

        # Get the additional info
        info = self.get_info()

        return observation, reward, terminated, False, info