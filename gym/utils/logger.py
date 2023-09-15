# SPDX-FileCopyrightText: Copyright (c) 2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Copyright (c) 2021 ETH Zurich, Nikita Rudin

import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from multiprocessing import Process, Value

class Logger:
    def __init__(self, dt):
        self.state_log = defaultdict(list)
        self.rew_log = defaultdict(list)
        self.dt = dt
        self.num_episodes = 0
        self.plot_process = None

    def log_state(self, key, value):
        self.state_log[key].append(value)

    def log_states(self, dict):
        for key, value in dict.items():
            self.log_state(key, value)

    def log_rewards(self, dict, num_episodes):
        for key, value in dict.items():
            try:
                self.rew_log[key].append(value.item() * num_episodes)
            except AttributeError:
                self.rew_log[key].append(value * num_episodes)
        self.num_episodes += num_episodes

    def reset(self):
        self.state_log.clear()
        self.rew_log.clear()

    def plot_states(self, log_file_path, visualize=True):
        self.plot_process = Process(target=self._plot(log_file_path, visualize))
        self.plot_process.start()

    def _plot(self, log_file_path, visualize):
        nb_rows = 3
        nb_cols = 4
        fig, axs = plt.subplots(nb_rows, nb_cols)
        for key, value in self.state_log.items():
            time = np.linspace(0, len(value)*self.dt, len(value))
            break
        log = self.state_log

        if log["oscillators"] and log["contact_forces_z"]:
            oscillators = np.array(log["oscillators"])
            oscillators_vel = np.array(log["oscillators_vel"])
            scaled_grf = np.array(log["grf"])

            forces = np.array(log["contact_forces_z"])
            time = np.transpose([time])
            vel_x = np.transpose(np.array([log["base_vel_x"]]))
            vel_target = np.transpose(np.array([log["command_x"]]))
            torques = np.array(log["torques"])
            velocities = np.array(log["velocities"])
            np.savetxt(log_file_path, np.hstack((time, vel_x, vel_target, oscillators, oscillators_vel, forces, scaled_grf, torques, velocities)), delimiter=",")
            for i in range(oscillators.shape[1]):
                #TODO: Change so that each [0,2pi) cycle is in a diff color
                a = axs[0, i]
                a.plot(oscillators[:, i], scaled_grf[:, i], label=f'force {i}')
                a.set(xlabel='phase [/]', ylabel='Forces z [/]', title='Vertical Contact forces normalized by body weight')
            for i in range(oscillators.shape[1]):
                #TODO: Currently shows jump from 2pi -> 0 clamp
                a = axs[1, i]
                a.scatter(oscillators[:, i], oscillators_vel[:, i], label=f'phase rate of change {i}')
                a.set(xlabel='phase [/]', ylabel='dt * phase rate of change [/]', title='Phase')
            for i in range(oscillators.shape[1]):
                a = axs[2, i]
                a.plot(time, oscillators[:, i], label=f'Phase over time {i}')
                a.set(xlabel='time [s]', ylabel='phase [/]', title='Phase')
        if visualize:
            plt.show()

        nb_rows = 3
        nb_cols = 3
        fig, axs = plt.subplots(nb_rows, nb_cols)
        # plot joint targets and measured positions
        a = axs[1, 0]
        if log["dof_pos"]: a.plot(time, log["dof_pos"], label='measured')
        if log["dof_pos_target"]: a.plot(time, log["dof_pos_target"], label='target')
        a.set(xlabel='time [s]', ylabel='Position [rad]', title='DOF Position')
        a.legend()
        # plot joint velocity
        a = axs[1, 1]
        if log["dof_vel"]: a.plot(time, log["dof_vel"], label='measured')
        if log["dof_vel_target"]: a.plot(time, log["dof_vel_target"], label='target')
        a.set(xlabel='time [s]', ylabel='Velocity [rad/s]', title='Joint Velocity')
        a.legend()
        # plot base vel x
        a = axs[0, 0]
        if log["base_vel_x"]: a.plot(time, log["base_vel_x"], label='measured')
        if log["command_x"]: a.plot(time, log["command_x"], label='commanded')
        a.set(xlabel='time [s]', ylabel='base lin vel [m/s]', title='Base velocity x')
        a.legend()
        # plot base vel y
        a = axs[0, 1]
        if log["base_vel_y"]: a.plot(time, log["base_vel_y"], label='measured')
        if log["command_y"]: a.plot(time, log["command_y"], label='commanded')
        a.set(xlabel='time [s]', ylabel='base lin vel [m/s]', title='Base velocity y')
        a.legend()
        # plot base vel yaw
        a = axs[0, 2]
        if log["base_vel_yaw"]: a.plot(time, log["base_vel_yaw"], label='measured')
        if log["command_yaw"]: a.plot(time, log["command_yaw"], label='commanded')
        a.set(xlabel='time [s]', ylabel='base ang vel [rad/s]', title='Base velocity yaw')
        a.legend()
        # plot base vel z
        a = axs[1, 2]
        if log["base_vel_z"]: a.plot(time, log["base_vel_z"], label='measured')
        a.set(xlabel='time [s]', ylabel='base lin vel [m/s]', title='Base velocity z')
        a.legend()
        # plot contact forces
        a = axs[2, 0]
        if log["contact_forces_z"]:
            forces = np.array(log["contact_forces_z"])
            for i in range(forces.shape[1]):
                a.plot(time, forces[:, i], label=f'force {i}')
        a.set(xlabel='time [s]', ylabel='Forces z [N]', title='Vertical Contact forces')
        a.legend()
        # plot torque/vel curves
        a = axs[2, 1]
        if log["dof_vel"]!=[] and log["dof_torque"]!=[]: a.plot(log["dof_vel"], log["dof_torque"], 'x', label='measured')
        a.set(xlabel='Joint vel [rad/s]', ylabel='Joint Torque [Nm]', title='Torque/velocity curves')
        a.legend()
        # plot torques
        a = axs[2, 2]
        if log["dof_torque"]!=[]: a.plot(time, log["dof_torque"], label='measured')
        a.set(xlabel='time [s]', ylabel='Joint Torque [Nm]', title='Torque')
        a.legend()
        if visualize:
            plt.show()

    def print_rewards(self, reward_file_path):
        print("Average rewards per second:")
        reward_keys = []
        reward_means = []
        for key, mean in self.rew_log.items():
            reward_keys = np.append(reward_keys, key)
            reward_means = np.append(reward_means, mean[0])
            print(f" - {key}: {mean}")
        reward_keys = np.append(reward_keys, "Total number of episodes")
        reward_means = np.append(reward_means, self.num_episodes)
        print(f"Total number of episodes: {self.num_episodes}")
        np.savetxt(reward_file_path, np.column_stack((reward_keys, reward_means)), delimiter=",", fmt="%s")

    def __del__(self):
        if self.plot_process is not None:
            self.plot_process.kill()