hatch-scanpy-typeshed
=====================

|PyPI Version| |PyPI Python Version| |Coverage|

What does it do?
----------------

For functions using keyword-only arguments (``*, copy: ...``),
it is able to clear up the function signature for ``copy``,
telling type checkers that a function returns ``None`` precisely when ``copy=False``,
and otherwise an ``AnnData`` instance.

E.g. when run on scanpy’s ``tl._score_genes`` module, it creates a ``.pyi`` file like this:

.. code:: python

   from collections.abc import Sequence
   from typing import Literal, overload
   from anndata import AnnData
   from .._utils import AnyRandom

   def score_genes(
       adata: AnnData, gene_list: Sequence[str], ctrl_size: int = ..., gene_pool: Sequence[str] | None = ...,
       n_bins: int = ..., score_name: str = ..., random_state: AnyRandom = ..., copy: bool = ..., use_raw: bool | None = ...,
   ) -> AnnData | None: ...
   @overload
   def score_genes_cell_cycle(adata: AnnData, s_genes: Sequence[str], g2m_genes: Sequence[str], copy: Literal[True], **kwargs) -> AnnData: ...
   @overload
   def score_genes_cell_cycle(adata: AnnData, s_genes: Sequence[str], g2m_genes: Sequence[str], copy: Literal[False] = False, **kwargs) -> None: ...

Together with (at the time of writing) a warning about a function that has not been converted to kw-only arguments yet:

.. code:: pytb

   UserWarning: Parameter 'copy' must be a keyword-only argument in scanpy.tools._score_genes function score_genes

Usage
-----

The plan is to soon include it as a plugin to a scanpy-like API’s ``pyproject.toml``:

.. code:: toml

   [build-system]
   requires = ["hatchling", "hatch-scanpy-typeshed"]
   build-backend = "hatchling.build"

License
-------

``hatch-scanpy-typeshed`` is distributed under the terms of the `GPL 3 (or later)`_ license.


.. |PyPI Version| image:: https://img.shields.io/pypi/v/hatch-scanpy-typeshed.svg
   :target: https://pypi.org/project/hatch-scanpy-typeshed
.. |PyPI Python Version| image:: https://img.shields.io/pypi/pyversions/hatch-scanpy-typeshed.svg
   :target: https://pypi.org/project/hatch-scanpy-typeshed
.. |Coverage| image:: https://codecov.io/github/flying-sheep/hatch-scanpy-typeshed/branch/main/graph/badge.svg?token=FZCw1cXSTL
   :target: https://codecov.io/github/flying-sheep/hatch-scanpy-typeshed

.. _GPL 3 (or later): https://spdx.org/licenses/GPL-3.0-or-later.html
