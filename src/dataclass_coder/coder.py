import json
from dataclasses import dataclass, is_dataclass
from functools import partial
from typing import TypeVar, Type, Optional, Any, Dict, Callable, ForwardRef, Union

T = TypeVar('T')


@dataclass
class FieldData:
    name: str
    type: Type[T]
    is_collection: bool = False
    collection: Type = None


SchemaDict = Dict[str, Dict[str, FieldData]]


def is_forwardref(obj: Any):
    return isinstance(obj, ForwardRef)


def is_generic(obj: Type):
    return hasattr(obj, '__origin__')


class DataclassCoder:
    def __init__(
            self,
            class_: Type[T],
            json_type_encoders: Optional[Dict[type, Callable[[Any], Any]]] = None,
            dict_type_decoders: Optional[Dict[type, Callable[[Any], Any]]] = None,
            dict_field_decoders: Optional[Dict[type, Dict[str, Callable[[Any], Any]]]] = None,
    ):
        self._class = class_
        self._module = self._class.__module__

        self.schema: SchemaDict = dict()
        self.get_schema(class_)
        self.objects = set()

        self.json_type_encoders = json_type_encoders or dict()
        self.dict_type_decoders = dict_type_decoders or dict()
        self.dict_field_decoders = dict_field_decoders or dict()

    def get_schema(self, class_: Type[T]):
        self.schema[class_] = {}
        for k, f in class_.__dataclass_fields__.items():
            type_, collection = self._get_type(f.type)
            self.schema[class_][f.name] = FieldData(f.name, type_, collection is not None, collection)
            if is_dataclass(type_):
                if type_ not in self.schema:
                    self.get_schema(type_)

    def _get_type(self, obj: Type):
        collection = None
        if is_generic(obj):
            origin = getattr(obj, '__origin__')
            if origin is not Union:
                collection = origin
            type_ = getattr(obj, '__args__')[0]
        else:
            type_ = obj
        if is_forwardref(type_):
            type_ = getattr(__import__(self._module), getattr(type_, '__forward_arg__'))
        if isinstance(type_, str):
            type_ = getattr(__import__(self._module), type_)
        return type_, collection

    def to_dict(self, obj: T) -> dict:
        self.objects.add(id(obj))
        result = self._to_dict(obj)
        self.objects.clear()
        return result

    def _to_dict(self, obj: T) -> dict:
        result = dict()
        for field in self.schema[obj.__class__].values():
            value = getattr(obj, field.name)
            if id(value) in self.objects:
                continue
            if field.is_collection:
                if field.type in self.schema:
                    result[field.name] = field.collection(map(self._to_dict, value))
                else:
                    result[field.name] = field.collection(map(field.type, value))
            else:
                if is_dataclass(field.type) and value is not None:
                    result[field.name] = self._to_dict(value)
                else:
                    result[field.name] = value
        return result

    def _json_field_serializer(self, obj: Any):
        return self.json_type_encoders[type(obj)](obj)

    def to_json(self, obj: T) -> str:
        return json.dumps(self.to_dict(obj), default=self._json_field_serializer)

    def _from_dict(self, data: Dict[str, Any], type_: Type = None):
        parsed = dict()
        if type_ is None:
            type_ = self._class
        for field in self.schema[type_].values():
            value = data.get(field.name)
            if field.is_collection:
                if field.type in self.schema:
                    parsed[field.name] = field.collection(map(partial(self._from_dict, type_=field.type), value))
                else:
                    parsed[field.name] = field.collection(map(field.type, value))
            elif field.type in self.schema:
                if value is not None:
                    parsed[field.name] = self._from_dict(value, field.type)
            else:
                if isinstance(value, field.type):
                    parsed[field.name] = value
                else:
                    if type_ in self.dict_field_decoders:
                        if field.name in self.dict_field_decoders[type_]:
                            parsed[field.name] = self.dict_field_decoders[type_][field.name](value)
                    elif field.type in self.dict_type_decoders:
                        parsed[field.name] = self.dict_type_decoders[type_](value)
                    else:
                        parsed[field.name] = field.type(value)
        return type_(**parsed)

    def from_dict(self, data: Dict[str, Any]) -> T:
        return self._from_dict(data)

    def from_json(self, json_str: str) -> T:
        return self.from_dict(json.loads(json_str))
