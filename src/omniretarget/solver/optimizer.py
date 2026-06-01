from __future__ import annotations

from typing import Any

import cvxpy as cp  # type: ignore[import-not-found]
import numpy as np
from scipy import sparse as sp  # type: ignore[import-untyped]

from omniretarget.solver.constraints import (
    foot_sticking_constraints,
    joint_limit_constraints,
    laplacian_equality_constraints,
    laplacian_objective_term,
    nominal_tracking_objective_term,
    non_penetration_constraints,
    q_diag_objective_term,
    smoothness_objective_term,
    trust_region_constraints,
)
from omniretarget.solver.frame_problem import FrameProblem, FrameSolution
from omniretarget.src.utils import calculate_laplacian_matrix


def solve_frame_problem(solver: Any, problem: FrameProblem) -> FrameSolution:
    """Solve one linearized interaction-mesh frame problem with CVXPY/Clarabel."""
    q_a_n_last = problem.q_a_n_last
    assert len(q_a_n_last) == solver.nq_a

    q = np.copy(problem.q_locked)
    q[solver.q_a_indices] = q_a_n_last

    J_OC_dict, p_OC_dict, _ = solver._calc_manipulator_jacobians(
        q,
        links=solver.laplacian_match_links,
        obj_frame=(solver.object_name != "ground"),
    )
    robot_link_keys = list(solver.laplacian_match_links.keys())
    V_r = len(robot_link_keys)
    V_o = len(problem.obj_pts_local)
    V = V_r + V_o

    J_V = np.zeros((3 * V, solver.nq_a))
    for i, key in enumerate(robot_link_keys):
        J_V[3 * i : 3 * (i + 1), :] = J_OC_dict[key]

    robot_pts_local = np.array([p_OC_dict[k] for k in robot_link_keys])
    vertices = np.vstack([robot_pts_local, problem.obj_pts_local])

    laplacian = calculate_laplacian_matrix(vertices, problem.adj_list)
    if not sp.issparse(laplacian):
        laplacian = sp.csr_matrix(laplacian)

    kron = sp.kron(laplacian, sp.eye(3, format="csr"), format="csr")
    J_L = kron @ J_V

    lap0 = laplacian @ vertices
    lap0_vec = lap0.reshape(-1)
    target_lap_vec = problem.target_laplacian.reshape(-1)

    w_v = (solver.laplacian_weights * np.ones(V)).astype(float)
    sqrt_w3 = np.sqrt(np.repeat(w_v, 3))

    dqa = cp.Variable(len(solver.q_a_indices), name="dqa")
    lap_var = cp.Variable(3 * V, name="laplacian")

    constraints = []
    constraints += laplacian_equality_constraints(J_L, solver.q_a_indices, dqa, lap_var, lap0_vec)
    constraints += foot_sticking_constraints(solver, q, problem.q_t_last, problem.foot_sticking, dqa)
    constraints += non_penetration_constraints(solver, q, dqa)
    constraints += joint_limit_constraints(solver, q_a_n_last, dqa)
    constraints += trust_region_constraints(solver.step_size, dqa)

    obj_terms = []
    obj_terms.append(laplacian_objective_term(sqrt_w3, lap_var, target_lap_vec))
    nominal_term = nominal_tracking_objective_term(
        solver.track_nominal_indices,
        problem.w_nominal_tracking,
        problem.q_a_nominal,
        q_a_n_last,
        dqa,
    )
    if nominal_term is not None:
        obj_terms.append(nominal_term)
    obj_terms.append(q_diag_objective_term(solver.Q_diag, q_a_n_last, dqa))
    obj_terms.append(
        smoothness_objective_term(
            solver.smooth_weight,
            problem.q_t_last,
            solver.q_a_indices,
            q_a_n_last,
            dqa,
        )
    )

    cvx_problem = cp.Problem(cp.Minimize(cp.sum(obj_terms)), constraints)
    solver_kwargs = {"verbose": problem.verbose}
    cvx_problem.solve(solver=cp.CLARABEL, **solver_kwargs)
    if (cvx_problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE)) and problem.init_t:
        constraints = [c for c in constraints if not isinstance(c, cp.constraints.second_order.SOC)]
        cvx_problem = cp.Problem(cp.Minimize(cp.sum(obj_terms)), constraints)
        cvx_problem.solve(solver=cp.CLARABEL, **solver_kwargs)

    if cvx_problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        raise RuntimeError(f"CVXPY solve failed: {cvx_problem.status}")

    dqa_star = dqa.value
    cost = cvx_problem.value

    q_star = np.copy(q)
    q_star[solver.q_a_indices] = dqa_star + q_a_n_last
    q_star[3:7] /= np.linalg.norm(q_star[3:7]) + 1e-12

    return FrameSolution(q=q_star, cost=float(cost))
