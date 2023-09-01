import importlib
import pkgutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Type, TypeVar, Optional, Set

from registrable import Registrable

T = TypeVar("T", bound="RegistrableFromDict")


class RegistrableFromDict(Registrable):
    """
    A super simplified version of Allennlp's FromParams, which doesn't
    recursively build nested objects, just the root-level one.
    """

    @classmethod
    def from_dict(cls: Type[T], dict_: dict) -> T:
        if "type" not in dict_:
            raise Exception("Missing 'type' in config dict.")
        class_type = dict_.pop("type")
        if not issubclass(cls, Registrable):
            raise Exception(
                f"The class {cls} is not a subclass of Registrable. Can't use from_dict without it.")
        if not cls.is_registered(class_type):
            raise Exception(
                f"The base class {cls} does not have any registered class as {class_type}.")
        sub_class = cls.by_name(class_type)
        instance = sub_class(**dict_)  # type: ignore
        return instance


"""
Functions borrowed from AllenNLP to load modules needed to run inference
"""


@contextmanager
def push_python_path(path):
    """
    Prepends the given path to `sys.path`.

    This method is intended to use with `with`, so after its usage, its value willbe removed from
    `sys.path`.
    """
    # In some environments, such as TC, it fails when sys.path contains a relative path, such as ".".
    path = Path(path).resolve()
    path = str(path)
    sys.path.insert(0, path)
    try:
        yield
    finally:
        # Better to remove by value, in case `sys.path` was manipulated in between.
        sys.path.remove(path)


def import_module_and_submodules(package_name: str, exclude: Optional[Set[str]] = None) -> None:
    """
    Import all public submodules under the given package.
    Primarily useful so that people using AllenNLP as a library
    can specify their own custom packages and have their custom
    classes get loaded and registered.
    """
    # take care of None
    exclude = exclude if exclude else set()

    if package_name in exclude:
        return

    importlib.invalidate_caches()

    # For some reason, python doesn't always add this by default to your path, but you pretty much
    # always want it when using `--include-package`.  And if it's already there, adding it again at
    # the end won't hurt anything.
    with push_python_path("."):
        # Import at top level
        module = importlib.import_module(package_name)
        path = getattr(module, "__path__", [])
        path_string = "" if not path else path[0]

        # walk_packages only finds immediate children, so need to recurse.
        for module_finder, name, _ in pkgutil.walk_packages(path):
            # Sometimes when you import third-party libraries that are on your path,
            # `pkgutil.walk_packages` returns those too, so we need to skip them.
            if path_string and module_finder.path != path_string:  # type: ignore[union-attr]
                continue
            if name.startswith("_"):
                # skip directly importing private subpackages
                continue
            if name.startswith("test"):
                # as long as allennlp.common.testing is not under tests/, exclude it
                continue
            subpackage = f"{package_name}.{name}"
            import_module_and_submodules(subpackage, exclude=exclude)
