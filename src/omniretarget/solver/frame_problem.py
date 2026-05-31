from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class FrameProblem:
    q_locked: np.ndarray
    q_a_n_last: np.ndarray
    q_t_last: np.ndarray
    target_laplacian: np.ndarray
    adj_list: list[list[int]]
    obj_pts_local: np.ndarray
    foot_sticking: dict[str, bool] | tuple[bool, bool] | Any
    w_nominal_tracking: float = 0.0
    q_a_nominal: np.ndarray | None = None
    verbose: bool = False
    init_t: bool = False


@dataclass(frozen=True)
class FrameSolution:
    q: np.ndarray
    cost: float
