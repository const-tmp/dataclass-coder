import json
from dataclasses import dataclass, MISSING, is_dataclass
from typing import TypeVar, Type, Optional, Any, Dict, Callable

T = TypeVar('T')


@dataclass
class FieldData:
    name: str
    type: Type[T]
    default: Optional[Any] = None


def get_fields(class_: type) -> Dict[str, FieldData]:
    fields: Dict[str, FieldData] = dict()
    for k, f in class_.__dataclass_fields__.items():
        default = None if f.default is MISSING else f.default
        if hasattr(f.type, '__origin__'):
            type_ = getattr(f.type, '__args__')[0]
        else:
            type_ = f.type
        fields[k] = FieldData(f.name, type_, default)
    return fields


class DataclassCoder:
    _class: Type[T]
    field_parsers: Optional[Dict[str, Callable[[Any], Any]]]
    type_parsers: Optional[Dict[type, Callable[[Any], Any]]]
    field_serializers: Optional[Dict[str, Callable[[Any], Any]]]
    type_serializers: Optional[Dict[type, Callable[[Any], Any]]]

    def __init__(
            self,
            class_: Type[T],
            field_parsers: Optional[Dict[str, Callable[[Any], Any]]] = None,
            type_parsers: Optional[Dict[type, Callable[[Any], Any]]] = None,
            field_serializers: Optional[Dict[str, Callable[[Any], Any]]] = None,
            type_serializers: Optional[Dict[type, Callable[[Any], Any]]] = None,
    ):
        self._class = class_

        self.field_parsers = field_parsers
        self.type_parsers = type_parsers

        self.field_serializers = field_serializers
        self.type_serializers = type_serializers

        self.fields: Dict[str, FieldData] = get_fields(self._class)

    def serialize(self, obj: T) -> Dict[str, Any]:
        data = dict()
        for field_name, field_data in self.fields.items():
            if is_dataclass(field_data.type):
                nested_coder = DataclassCoder(field_data.type, field_serializers=self.field_serializers,
                                              type_serializers=self.type_serializers)
                data[field_name] = nested_coder.serialize(getattr(obj, field_name))
            else:
                data[field_name] = getattr(obj, field_name)
        return data

    def parse(self, data: Dict[str, Any]) -> T:
        parsed = dict()
        for field_name, field_data in self.fields.items():
            if field_name in data:
                value = data[field_name]
                if isinstance(value, field_data.type):
                    parsed[field_name] = value
                elif is_dataclass(field_data.type):
                    nested_coder = DataclassCoder(
                        field_data.type,
                        field_parsers=self.field_parsers,
                        type_parsers=self.type_parsers
                    )
                    parsed[field_name] = nested_coder.parse(value)
                elif self.field_parsers is not None and field_name in self.field_parsers:
                    parsed[field_name] = self.field_parsers[field_name](value)
                elif self.type_parsers is not None and field_data.type in self.type_parsers:
                    parsed[field_name] = self.type_parsers[field_data.type](value)
                else:
                    parsed[field_name] = field_data.type(value)
        return self._class(**parsed)

    def _json_field_serializer(self, obj: Any):
        return self.type_serializers[type(obj)](obj)

    def to_json(self, obj: T) -> str:
        return json.dumps(self.serialize(obj), default=self._json_field_serializer)

    def from_json(self, json_str: str) -> T:
        return self.parse(json.loads(json_str))
