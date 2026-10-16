"""Shared helpers for the patches of this project.

Patches are imported as modules whose dotted name starts at the project root, so
this package is importable from any patch with an absolute import:

    from patch_lib import mcmeta

Keep it in the project root. A .py file placed inside a version directory is
treated as a patch instead, and the framework will try to run it.
"""
