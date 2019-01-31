#!/usr/bin/env python3

import torch
from ..lazy import LazyTensor


class NonLazyTensor(LazyTensor):
    def __init__(self, tsr):
        """
        Not a lazy tensor

        Args:
        - tsr (Tensor: matrix) a Tensor
        """
        if not torch.is_tensor(tsr):
            raise RuntimeError("NonLazyTensor must take a torch.Tensor; got {}".format(tsr.__class__.__name__))

        super(NonLazyTensor, self).__init__(tsr)
        self.tensor = tsr

    def _expand_batch(self, batch_shape):
        return self.__class__(self.tensor.expand(*batch_shape, *self.matrix_shape))

    def _getitem(self, row_col_are_absorbed, row_index, col_index, *batch_indices):
        # Perform the __getitem__
        res = self.tensor[(*batch_indices, row_index, col_index)]
        if not row_col_are_absorbed:
            res = NonLazyTensor(res)
        return res

    def _matmul(self, rhs):
        return torch.matmul(self.tensor, rhs)

    def _quad_form_derivative(self, left_vecs, right_vecs):
        res = left_vecs.matmul(right_vecs.transpose(-1, -2))
        return (res,)

    def _size(self):
        return self.tensor.size()

    def _transpose_nonbatch(self):
        return NonLazyTensor(self.tensor.transpose(-1, -2))

    def _t_matmul(self, rhs):
        return torch.matmul(self.tensor.transpose(-1, -2), rhs)

    def diag(self):
        if self.tensor.ndimension() < 3:
            return self.tensor.diag()
        else:
            row_col_iter = torch.arange(0, self.matrix_shape[-1], dtype=torch.long, device=self.device)
            return self.tensor[..., row_col_iter, row_col_iter].view(*self.batch_shape, -1)

    def evaluate(self):
        return self.tensor


def lazify(obj):
    """
    A function which ensures that `obj` is a LazyTensor.

    If `obj` is a LazyTensor, this function does nothing.
    If `obj` is a (normal) Tensor, this function wraps it with a `NonLazyTensor`.
    """

    if torch.is_tensor(obj):
        return NonLazyTensor(obj)
    elif isinstance(obj, LazyTensor):
        return obj
    else:
        raise TypeError("object of class {} cannot be made into a LazyTensor".format(obj.__class__.__name__))


__all__ = [
    "NonLazyTensor",
    "lazify",
]
