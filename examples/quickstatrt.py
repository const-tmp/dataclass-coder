from dataclasses import dataclass
from datetime import date

from dataclass_coder import DataclassCoder


@dataclass
class Person:
    name: str
    age: int
    birthday: date


person_coder = DataclassCoder(Person,
                              field_parsers={'birthday': date.fromisoformat},
                              type_serializers={date: date.isoformat})

data = '{"name": "High Time", "age": 30, "birthday": "1991-04-01"}'

person = person_coder.from_json(data)
print(person)  # Person(name='High Time', age=30, birthday=datetime.date(1991, 4, 1))

person_dict = person_coder.serialize(person)
print(person_dict)  # {'name': 'High Time', 'age': 30, 'birthday': datetime.date(1991, 4, 1)}

person_json = person_coder.to_json(person)
print(person_json)  # {"name": "High Time", "age": 30, "birthday": "1991-04-01"}
