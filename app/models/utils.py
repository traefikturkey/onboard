import base64
import hashlib
import logging
import os
from pathlib import Path
import re
from typing import Any, List, TypeVar, Callable, Type, cast

import unidecode
T = TypeVar("T")

pwd = Path(os.path.dirname(os.path.realpath(__file__))).parent

def from_str(x: Any) -> str:
	assert isinstance(x, str)
	return x


def from_list(f: Callable[[Any], T], x: Any, parent: Any = None) -> List[T]:
	assert isinstance(x, list)
	if parent is None:
		return [f(y) for y in x]
	else:
		return [f(y, parent) for y in x]



def from_none(x: Any) -> Any:
	assert x is None
	return x


def from_union(fs, x):
	for f in fs:
		try:
			return f(x)
		except:
			pass
	assert False


def to_class(c: Type[T], x: Any) -> dict:
	assert isinstance(x, c)
	return cast(Any, x).to_dict()


def from_bool(x: Any) -> bool:
	assert isinstance(x, bool)
	return x


def from_int(x: Any) -> int:
	assert isinstance(x, int) and not isinstance(x, bool)
	return x

def normalize_text(text: str) -> str:
	text = unidecode.unidecode(text)
	text = re.sub(r'&#8220;|&#8221;', '"', text)
	text = re.sub(r'&#8217;|&#8216;', "'", text)
	return re.sub(r'\s+|\n|\r', ' ',text).strip()

def calculate_sha1_hash(value: str) -> str:
		sha1 = hashlib.sha1()
		sha1.update(value.encode('utf-8'))
		hash = base64.urlsafe_b64encode(sha1.digest()).decode('ascii')
		return ''.join(filter(str.isalnum, hash))

def to_snake_case(input_string):
		# Replace non-alphanumeric characters and apostrophes with spaces and split the string into words
		words = re.findall(r"[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?", input_string)

		# Remove apostrophes from the words
		words = [word.replace("'", "") for word in words]

		# Convert words to lowercase and join them with underscores
		snake_case_string = '_'.join(word.lower() for word in words)

		return snake_case_string
