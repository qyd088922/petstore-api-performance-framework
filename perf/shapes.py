# -*- coding: utf-8 -*-
"""LoadTestShape 负载模型：正弦、阶梯、多波形叠加。

模拟真实流量曲线，而不是恒定并发。tick() 返回 (user_count, spawn_rate)，
返回 None 表示压测结束。
"""
import math

from locust import LoadTestShape

from config.perf_config import SHAPE_DURATION, SHAPE_MAX_USERS


class StepShape(LoadTestShape):
    """阶梯加压：按固定步长逐级提升并发，观察容量拐点。"""

    step_users = 10
    step_seconds = 10

    def tick(self):
        run_time = self.get_run_time()
        if run_time > SHAPE_DURATION:
            return None
        level = int(run_time // self.step_seconds) + 1
        users = min(level * self.step_users, SHAPE_MAX_USERS)
        return users, self.step_users


class SineShape(LoadTestShape):
    """正弦波形：模拟日内潮汐流量，低谷->高峰->低谷平滑波动。"""

    period = 30

    def tick(self):
        run_time = self.get_run_time()
        if run_time > SHAPE_DURATION:
            return None
        # 0..1 归一化的正弦，抬升到 [min_users, max_users]
        wave = (math.sin(2 * math.pi * run_time / self.period - math.pi / 2) + 1) / 2
        users = int(SHAPE_MAX_USERS * (0.2 + 0.8 * wave))
        return max(users, 1), 5


class MultiWaveShape(LoadTestShape):
    """多波形叠加：长期上升基数 + 中周期波动 + 短周期尖峰，逼近真实业务曲线。"""

    def tick(self):
        run_time = self.get_run_time()
        if run_time > SHAPE_DURATION:
            return None
        base = SHAPE_MAX_USERS * 0.5 * (run_time / SHAPE_DURATION)   # 长期爬坡
        mid = SHAPE_MAX_USERS * 0.25 * math.sin(2 * math.pi * run_time / 25)
        spike = SHAPE_MAX_USERS * 0.15 * max(0, math.sin(2 * math.pi * run_time / 7))
        users = int(base + mid + spike)
        return max(users, 1), 5
