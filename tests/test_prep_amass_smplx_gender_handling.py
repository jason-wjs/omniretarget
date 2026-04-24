import numpy as np
import torch

from holosoma_retargeting.cli.data_process.prep_amass_smplx_for_rt import run_smplx_model


class _DummyPredBody:
    def __init__(self, batch_size: int) -> None:
        self.Jtr = torch.zeros((batch_size, 52, 3), dtype=torch.float32)
        self.v = torch.zeros((batch_size, 10, 3), dtype=torch.float32)
        self.f = torch.tensor([[0, 1, 2]], dtype=torch.int64)


class _DummyBodyModel:
    def __call__(self, pose_body, pose_hand, betas, root_orient, trans):  # noqa: ANN001
        return _DummyPredBody(batch_size=trans.shape[0])


def test_run_smplx_model_uses_neutral_model_for_non_neutral_amass_gender() -> None:
    root_trans = torch.zeros((1, 4, 3), dtype=torch.float32)
    aa_rot_rep = torch.zeros((1, 4, 52, 3), dtype=torch.float32)
    betas = torch.zeros((1, 16), dtype=torch.float32)
    bm_dict = {"neutral": _DummyBodyModel()}

    joints, verts, _faces = run_smplx_model(
        root_trans=root_trans,
        aa_rot_rep=aa_rot_rep,
        betas=betas,
        gender=[np.str_("male")],
        bm_dict=bm_dict,
    )

    assert joints.shape == (1, 4, 52, 3)
    assert verts.shape == (1, 4, 10, 3)
