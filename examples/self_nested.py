from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from dataclass_coder import DataclassCoder


@dataclass
class Person:
    name: str
    age: int
    birthday: date
    friend: Optional['Person'] = None


person_coder = DataclassCoder(Person,
                              field_parsers={'birthday': date.fromisoformat, 'decimal_value': Decimal},
                              type_serializers={date: date.isoformat, Decimal: str})


data = '{"name": "High Time", "age": 26, "birthday": "1995-04-01", "friend": {"name": "All Cats", "age": 26, "birthday": "1995-04-12"}}'

person = person_coder.from_json(data)
print(person)  # Person(name='High Time', age=26, birthday=datetime.date(1995, 4, 1), nested_field=NestedField(name='test', decimal_value=Decimal('11.1')))

person_dict = person_coder.serialize(person)
print(person_dict)  # {'name': 'High Time', 'age': 26, 'birthday': datetime.date(1995, 4, 1), 'nested_field': {'name': 'test', 'decimal_value': Decimal('11.1')}}

person_json = person_coder.to_json(person)
print(person_json)  # {"name": "High Time", "age": 26, "birthday": "1995-04-01", "nested_field": {"name": "test", "decimal_value": "11.1"}}
