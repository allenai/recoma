from registrable import Registrable
from typing import Type, TypeVar

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
        instance = sub_class(**dict_) # type: ignore
        return instance
