from abc import ABC
from typing import Callable, List, Sized, Type, Union

from . import Crypto
from .. import lists

class SymEncScheme(Crypto.Scheme, ABC):
    class SecretKey(): pass
    class Ciphertext(): pass
    class Message(Sized): pass
    @staticmethod
    def KeyGen() -> SecretKey: pass
    @staticmethod
    def Encrypt(k: SecretKey, msg: Message) -> Ciphertext: pass
    @staticmethod
    def Decrypt(k: SecretKey, ct: Ciphertext) -> Union[Message, Crypto.Reject]: pass

# the following definitions are based on https://eprint.iacr.org/2000/025.pdf

class INDCPA_LOR_Adversary(Crypto.Adversary):
    def run(self, o_LR: Callable[[SymEncScheme.Message, SymEncScheme.Message], SymEncScheme.Ciphertext]) -> Crypto.Bit: pass

class INDCPA_LOR_Game(Crypto.GameParameterizedByBit):
    def __init__(self, Scheme: Type[SymEncScheme], Adversary: Type[INDCPA_LOR_Adversary], b: Crypto.Bit):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
        self.b = b
    def main(self) -> Crypto.Bit:
        self.k = self.Scheme.KeyGen()
        bprime = self.adversary.run(self.o_LR)
        return bprime
    def o_LR(self, m0: SymEncScheme.Message, m1: SymEncScheme.Message) -> SymEncScheme.Ciphertext:
        m = m0 if self.b == 0 else m1
        c = self.Scheme.Encrypt(self.k, m)
        return c

INDCPA_LOR = Crypto.DistinguishingExperimentHiddenBit(INDCPA_LOR_Game, INDCPA_LOR_Adversary)

class INDCCA_LOR_Adversary(Crypto.Adversary):
    def run(self, o_LR: Callable[[SymEncScheme.Message, SymEncScheme.Message], SymEncScheme.Ciphertext], o_Dec: Callable[[SymEncScheme.Ciphertext], Union[SymEncScheme.Message, Crypto.Reject]]) -> Crypto.Bit: pass

class INDCCA_LOR_Game(Crypto.GameParameterizedByBit):
    def __init__(self, Scheme: Type[SymEncScheme], Adversary: Type[INDCCA_LOR_Adversary], b: Crypto.Bit):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
        self.b = b
    def main(self) -> Crypto.Bit:
        self.k = self.Scheme.KeyGen()
        self.ciphertexts = lists.new_empty_list()
        bprime = self.adversary.run(self.o_LR, self.o_Dec)
        return bprime
    def o_LR(self, m0: SymEncScheme.Message, m1: SymEncScheme.Message) -> SymEncScheme.Ciphertext:
        m = m0 if self.b == 0 else m1
        c = self.Scheme.Encrypt(self.k, m)
        self.ciphertexts = lists.append_item(self.ciphertexts, c)
        return c
    def o_Dec(self, c: SymEncScheme.Ciphertext) -> Union[SymEncScheme.Message, Crypto.Reject]:
        if not(c in self.ciphertexts): m = self.Scheme.Decrypt(self.k, c)
        else: m = Crypto.Reject()
        return m

INDCCA_LOR = Crypto.DistinguishingExperimentHiddenBit(INDCCA_LOR_Game, INDCCA_LOR_Adversary)

class INT_PTXT_Adversary(Crypto.Adversary):
    def run(self, o_Enc: Callable[[SymEncScheme.Message], SymEncScheme.Ciphertext], o_VF: Callable[[SymEncScheme.Ciphertext], bool]) -> Crypto.Bit: pass

class INT_PTXT_Game(Crypto.Game):
    def __init__(self, Scheme: Type[SymEncScheme], Adversary: Type[INT_PTXT_Adversary], b: Crypto.Bit):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.win = Crypto.Bit(0)
        self.k = self.Scheme.KeyGen()
        self.messages = lists.new_empty_list()
        self.adversary.run(self.o_Enc, self.o_VF)
        return self.win
    def o_Enc(self, m: SymEncScheme.Message) -> SymEncScheme.Ciphertext:
        c = self.Scheme.Encrypt(self.k, m)
        self.messages = lists.append_item(self.messages, m)
        return c
    def o_VF(self, c: SymEncScheme.Ciphertext) -> bool:
        m = self.Scheme.Decrypt(self.k, c)
        if not(isinstance(m, Crypto.Reject)) and not(m in self.messages): self.win = Crypto.Bit(1)
        ret = not(isinstance(m, Crypto.Reject))
        return ret

INT_PTXT = Crypto.WinLoseExperiment(INT_PTXT_Game, INT_PTXT_Adversary)
