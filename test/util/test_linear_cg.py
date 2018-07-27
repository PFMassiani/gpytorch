from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import random
import torch
import unittest
from gpytorch.utils import approx_equal, batch_potrf, batch_potrs
from gpytorch.utils.linear_cg import linear_cg


class TestLinearCG(unittest.TestCase):
    def setUp(self):
        if os.getenv("UNLOCK_SEED") is None or os.getenv("UNLOCK_SEED").lower() == "false":
                self.rng_state = torch.get_rng_state()
                torch.manual_seed(0)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed_all(0)
                random.seed(0)

    def tearDown(self):
        if hasattr(self, "rng_state"):
            torch.set_rng_state(self.rng_state)

    def test_cg(self):
        size = 100
        matrix = torch.DoubleTensor(size, size).normal_()
        matrix = matrix.matmul(matrix.transpose(-1, -2))
        matrix.div_(matrix.norm())
        matrix.add_(torch.DoubleTensor(matrix.size(-1)).fill_(1e-1).diag())

        rhs = torch.DoubleTensor(size, 50).normal_()
        solves = linear_cg(matrix.matmul, rhs=rhs, max_iter=size)

        # Check cg
        matrix_chol = matrix.potrf()
        actual = torch.potrs(rhs, matrix_chol)
        self.assertTrue(approx_equal(solves, actual))

    def test_cg_with_tridiag(self):
        size = 10
        matrix = torch.DoubleTensor(size, size).normal_()
        matrix = matrix.matmul(matrix.transpose(-1, -2))
        matrix.div_(matrix.norm())
        matrix.add_(torch.DoubleTensor(matrix.size(-1)).fill_(1e-1).diag())

        rhs = torch.DoubleTensor(size, 50).normal_()
        solves, t_mats = linear_cg(matrix.matmul, rhs=rhs, n_tridiag=5, max_tridiag_iter=10, max_iter=size, tolerance=0)

        # Check cg
        matrix_chol = matrix.potrf()
        actual = torch.potrs(rhs, matrix_chol)
        self.assertTrue(approx_equal(solves, actual))

        # Check tridiag
        eigs = matrix.symeig()[0]
        for i in range(5):
            approx_eigs = t_mats[i].symeig()[0]
            self.assertTrue(approx_equal(eigs, approx_eigs))

    def test_batch_cg(self):
        batch = 5
        size = 100
        matrix = torch.DoubleTensor(batch, size, size).normal_()
        matrix = matrix.matmul(matrix.transpose(-1, -2))
        matrix.div_(matrix.norm())
        matrix.add_(torch.DoubleTensor(matrix.size(-1)).fill_(1e-1).diag())

        rhs = torch.DoubleTensor(batch, size, 50).normal_()
        solves = linear_cg(matrix.matmul, rhs=rhs, max_iter=size)

        # Check cg
        matrix_chol = batch_potrf(matrix)
        actual = batch_potrs(rhs, matrix_chol)
        self.assertTrue(approx_equal(solves, actual))

    def test_batch_cg_with_tridiag(self):
        batch = 5
        size = 10
        matrix = torch.DoubleTensor(batch, size, size).normal_()
        matrix = matrix.matmul(matrix.transpose(-1, -2))
        matrix.div_(matrix.norm())
        matrix.add_(torch.DoubleTensor(matrix.size(-1)).fill_(1e-1).diag())

        rhs = torch.DoubleTensor(batch, size, 50).normal_()
        solves, t_mats = linear_cg(matrix.matmul, rhs=rhs, n_tridiag=8, max_iter=size, max_tridiag_iter=10, tolerance=0)

        # Check cg
        matrix_chol = batch_potrf(matrix)
        actual = batch_potrs(rhs, matrix_chol)
        self.assertTrue(approx_equal(solves, actual))

        # Check tridiag
        for i in range(5):
            eigs = matrix[i].symeig()[0]
            for j in range(8):
                approx_eigs = t_mats[j, i].symeig()[0]
                self.assertLess(torch.mean(torch.abs((eigs - approx_eigs) / eigs)), 0.05)


if __name__ == "__main__":
    unittest.main()
