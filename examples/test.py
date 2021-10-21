from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional, List, Tuple, Set, Dict

from dataclass_coder import DataclassCoder


@dataclass
class Data:
    a: str
    # test: 'Test'


@dataclass
class Test:
    string: str
    digit: int
    li: List[int]
    # ti: Tuple[int]
    # si: Set[int]
    # di: Dict[int, int]
    data: Data
    data_list: List['Data']


test_coder = DataclassCoder(Test)

test_data = Test(string='asadsf', li=[1, 23, 234, 5, 4534, 653, 65], digit=234234, data=Data(a='sfgdfg'),
                 data_list=[Data(a='aaaaaaaa'), Data(a='bbbbb')])

d = test_coder.to_dict(test_data)
print(d)
print(test_coder.to_json(test_data))

print(test_coder.from_dict(d))
