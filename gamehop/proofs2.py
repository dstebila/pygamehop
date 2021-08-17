from abc import ABC
import inspect
from typing import List, Type
import typing
import ast
import jinja2

from .primitives import Crypto
from . import inlining
from .inlining import internal
from . import verification
from . import utils

class Proof():
    def __init__(self, scheme: Type[Crypto.Scheme], experiment: Crypto.Experiment):
        self.scheme = scheme
        self.experiment = experiment
