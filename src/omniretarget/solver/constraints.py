from __future__ import annotations

from collections.abc import Mapping

import cvxpy as cp  # type: ignore[import-not-found]
import numpy as np


def select_bilateral_foot_keys(foot_sticking: Mapping[str, bool]) -> tuple[str, str]:
    """Return the first left/right keys from a foot-sticking contact mapping."""
    left_key = next((key for key in foot_sticking if key.lower().startswith("l")), None)
    right_key = next((key for key in foot_sticking if key.lower().startswith("r")), None)
    if left_key is None or right_key is None:
        raise ValueError("foot_sticking must include one left* and one right* key")
    return left_key, right_key


def laplacian_equality_constraints(J_L, q_a_indices: np.ndarray, dqa, lap_var, lap0_vec: np.ndarray) -> list:
    """Build the linearized Laplacian equality constraint."""
    return [cp.Constant(J_L[:, q_a_indices]) @ dqa - lap_var == -lap0_vec]


def foot_sticking_constraints(solver, q: np.ndarray, q_t_last: np.ndarray, foot_sticking, dqa) -> list:
    """Build active foot-sticking box constraints."""
    if not ((solver.q_a_init_idx < 12) and solver.activate_foot_sticking):
        return []

    J_WF_dict, p_WF_dict, _ = solver._calc_manipulator_jacobians(q, links=solver.foot_links, obj_frame=False)
    _, p_WF_t_last_dict, _ = solver._calc_manipulator_jacobians(
        q_t_last,
        links=solver.foot_links,
        obj_frame=False,
    )
    left_key, right_key = select_bilateral_foot_keys(foot_sticking)

    constraints = []
    for key, J_WF in J_WF_dict.items():
        apply_left = ("left" in key) and foot_sticking[left_key]
        apply_right = ("right" in key) and foot_sticking[right_key]
        if apply_left or apply_right:
            p_lb = p_WF_t_last_dict[key] - p_WF_dict[key] - solver.foot_sticking_tolerance
            p_ub = p_lb + 2 * solver.foot_sticking_tolerance

            Jxy = J_WF[:2, solver.q_a_indices]
            constraints += [
                Jxy @ dqa >= p_lb[:2],
                Jxy @ dqa <= p_ub[:2],
            ]
    return constraints


def non_penetration_constraints(solver, q: np.ndarray, dqa) -> list:
    """Build active non-penetration constraints from current MuJoCo distances."""
    Js, phis = solver._update_jacobians_and_phis_from_q(q)
    constraints = []
    for key, phi in phis.items():
        if not solver._should_enforce_non_penetration_pair(key):
            continue
        Ja_n_full = Js[key]
        Ja_n = Ja_n_full[solver.q_a_indices]
        rhs = -phi - solver.penetration_tolerance
        constraints += [Ja_n @ dqa >= rhs]
    return constraints


def joint_limit_constraints(solver, q_a_n_last: np.ndarray, dqa) -> list:
    """Build actuated joint limit constraints when enabled."""
    if not solver.activate_joint_limits:
        return []
    return [
        dqa >= (solver.q_a_lb - q_a_n_last),
        dqa <= (solver.q_a_ub - q_a_n_last),
    ]


def trust_region_constraints(step_size: float, dqa) -> list:
    """Build the SQP trust-region constraint."""
    return [cp.SOC(step_size, dqa)]


def laplacian_objective_term(sqrt_w3: np.ndarray, lap_var, target_lap_vec: np.ndarray):
    """Build the weighted Laplacian target objective term."""
    return cp.sum_squares(cp.multiply(sqrt_w3, lap_var - target_lap_vec))


def nominal_tracking_objective_term(
    track_nominal_indices: np.ndarray,
    w_nominal_tracking: float,
    q_a_nominal: np.ndarray | None,
    q_a_n_last: np.ndarray,
    dqa,
):
    """Build nominal tracking objective term when enabled."""
    if (w_nominal_tracking <= 0) or (q_a_nominal is None):
        return None
    idx = np.array(track_nominal_indices, dtype=int)
    if idx.size == 0:
        return None
    z = dqa[idx] - (q_a_nominal[idx] - q_a_n_last[idx])
    return w_nominal_tracking * cp.sum_squares(z)


def q_diag_objective_term(Q_diag: np.ndarray, q_a_n_last: np.ndarray, dqa):
    """Build the diagonal joint prior objective term."""
    Qd = np.asarray(Q_diag, dtype=float).reshape(-1)
    return cp.sum_squares(cp.multiply(np.sqrt(Qd), dqa + q_a_n_last))


def smoothness_objective_term(smooth_weight, q_t_last: np.ndarray, q_a_indices: np.ndarray, q_a_n_last: np.ndarray, dqa):
    """Build the trajectory smoothness objective term."""
    dqa_smooth = q_t_last[q_a_indices] - q_a_n_last
    if np.isscalar(smooth_weight):
        return smooth_weight * cp.sum_squares(dqa - dqa_smooth)

    Wsmooth = np.asarray(smooth_weight, dtype=float)
    if Wsmooth.ndim == 1:
        return cp.sum_squares(cp.multiply(np.sqrt(Wsmooth), dqa - dqa_smooth))
    return cp.quad_form(dqa - dqa_smooth, Wsmooth)
