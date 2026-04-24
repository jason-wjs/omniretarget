from __future__ import annotations

import cvxpy as cp  # type: ignore[import-not-found]
import numpy as np
from scipy import sparse as sp  # type: ignore[import-untyped]

from holosoma_retargeting.retargeter.constraint import calc_manipulator_jacobians
from holosoma_retargeting.retargeter.constraint import update_jacobians_and_phis_from_q
from holosoma_retargeting.retargeter.interaction_mesh import calculate_laplacian_matrix


def solve_sqp_step(
    retargeter,
    q_locked: np.ndarray,
    q_a_n_last: np.ndarray,
    q_t_last: np.ndarray,
    target_laplacian: np.ndarray,
    adj_list: list[list[int]],
    obj_pts_local: np.ndarray,
    foot_sticking: tuple[bool, bool],
    w_nominal_tracking: float = 0.0,
    q_a_nominal: np.ndarray | None = None,
    verbose=False,
    init_t=False,
):
    """Build and solve one SQP step for interaction-mesh retargeting."""
    assert len(q_a_n_last) == retargeter.nq_a

    q = np.copy(q_locked)
    q[retargeter.q_a_indices] = q_a_n_last

    J_OC_dict, p_OC_dict, _ = calc_manipulator_jacobians(
        retargeter,
        q,
        links=retargeter.laplacian_match_links,
        obj_frame=(retargeter.object_name != "ground"),
    )
    robot_link_keys = list(retargeter.laplacian_match_links.keys())
    n_robot_vertices = len(robot_link_keys)
    n_object_vertices = len(obj_pts_local)
    n_vertices = n_robot_vertices + n_object_vertices

    J_V = np.zeros((3 * n_vertices, retargeter.nq_a))
    for i, key in enumerate(robot_link_keys):
        J_V[3 * i : 3 * (i + 1), :] = J_OC_dict[key]

    robot_pts_local = np.array([p_OC_dict[k] for k in robot_link_keys])
    vertices = np.vstack([robot_pts_local, obj_pts_local])

    laplacian_matrix = calculate_laplacian_matrix(vertices, adj_list)
    if not sp.issparse(laplacian_matrix):
        laplacian_matrix = sp.csr_matrix(laplacian_matrix)

    kron = sp.kron(laplacian_matrix, sp.eye(3, format="csr"), format="csr")
    J_L = kron @ J_V

    lap0 = laplacian_matrix @ vertices
    lap0_vec = lap0.reshape(-1)
    target_lap_vec = target_laplacian.reshape(-1)

    vertex_weights = (retargeter.laplacian_weights * np.ones(n_vertices)).astype(float)
    sqrt_w3 = np.sqrt(np.repeat(vertex_weights, 3))

    dqa = cp.Variable(len(retargeter.q_a_indices), name="dqa")
    lap_var = cp.Variable(3 * n_vertices, name="laplacian")

    constraints = []
    constraints += [cp.Constant(J_L[:, retargeter.q_a_indices]) @ dqa - lap_var == -lap0_vec]

    if (retargeter.q_a_init_idx < 12) and retargeter.activate_foot_sticking:
        J_WF_dict, p_WF_dict, _ = calc_manipulator_jacobians(
            retargeter,
            q,
            links=retargeter.foot_links,
            obj_frame=False,
        )
        _, p_WF_t_last_dict, _ = calc_manipulator_jacobians(
            retargeter,
            q_t_last,
            links=retargeter.foot_links,
            obj_frame=False,
        )
        left_key = right_key = None
        for key in foot_sticking:
            if key.lower().startswith("l"):
                left_key = key
            elif key.lower().startswith("r"):
                right_key = key
        if left_key is None or right_key is None:
            raise ValueError("foot_sticking must include one left* and one right* key")

        for key, J_WF in J_WF_dict.items():
            apply_left = ("left" in key) and foot_sticking[left_key]
            apply_right = ("right" in key) and foot_sticking[right_key]
            if apply_left or apply_right:
                p_lb = p_WF_t_last_dict[key] - p_WF_dict[key] - retargeter.foot_sticking_tolerance
                p_ub = p_lb + 2 * retargeter.foot_sticking_tolerance

                Jxy = J_WF[:2, retargeter.q_a_indices]
                constraints += [
                    Jxy @ dqa >= p_lb[:2],
                    Jxy @ dqa <= p_ub[:2],
                ]

    jacobians, phis = update_jacobians_and_phis_from_q(retargeter, q)
    for key, phi in phis.items():
        Ja_n_full = jacobians[key]
        Ja_n = Ja_n_full[retargeter.q_a_indices]
        rhs = -phi - retargeter.penetration_tolerance
        constraints += [Ja_n @ dqa >= rhs]

    if retargeter.activate_joint_limits:
        constraints += [
            dqa >= (retargeter.q_a_lb - q_a_n_last),
            dqa <= (retargeter.q_a_ub - q_a_n_last),
        ]

    constraints += [cp.SOC(retargeter.step_size, dqa)]

    obj_terms = []
    obj_terms.append(cp.sum_squares(cp.multiply(sqrt_w3, lap_var - target_lap_vec)))

    if (w_nominal_tracking > 0) and (q_a_nominal is not None):
        idx = np.array(retargeter.track_nominal_indices, dtype=int)
        if idx.size > 0:
            z = dqa[idx] - (q_a_nominal[idx] - q_a_n_last[idx])
            obj_terms.append(w_nominal_tracking * cp.sum_squares(z))

    q_cost = np.asarray(retargeter.Q_diag, dtype=float).reshape(-1)
    obj_terms.append(cp.sum_squares(cp.multiply(np.sqrt(q_cost), dqa + q_a_n_last)))

    dqa_smooth = q_t_last[retargeter.q_a_indices] - q_a_n_last
    if np.isscalar(retargeter.smooth_weight):
        obj_terms.append(retargeter.smooth_weight * cp.sum_squares(dqa - dqa_smooth))
    else:
        smooth_weights = np.asarray(retargeter.smooth_weight, dtype=float)
        if smooth_weights.ndim == 1:
            obj_terms.append(cp.sum_squares(cp.multiply(np.sqrt(smooth_weights), dqa - dqa_smooth)))
        else:
            obj_terms.append(cp.quad_form(dqa - dqa_smooth, smooth_weights))

    problem = cp.Problem(cp.Minimize(cp.sum(obj_terms)), constraints)

    solver_kwargs = {"verbose": verbose}
    problem.solve(solver=cp.CLARABEL, **solver_kwargs)
    if (problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE)) and init_t:
        constraints = [c for c in constraints if not isinstance(c, cp.constraints.second_order.SOC)]
        problem = cp.Problem(cp.Minimize(cp.sum(obj_terms)), constraints)
        problem.solve(solver=cp.CLARABEL, **solver_kwargs)

    if problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        raise RuntimeError(f"CVXPY solve failed: {problem.status}")

    dqa_star = dqa.value
    cost = problem.value

    q_star = np.copy(q)
    q_star[retargeter.q_a_indices] = dqa_star + q_a_n_last
    q_star[3:7] /= np.linalg.norm(q_star[3:7]) + 1e-12

    return q_star, cost
