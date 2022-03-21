from typing import Annotated, Callable, Generic, Type, TypeVar

from . import Crypto
from .. import lists

Key = TypeVar('Key')
Message = TypeVar('Message')
Ciphertext = TypeVar('Ciphertext')

class SymEncScheme(Crypto.Scheme, Generic[Key, Message, Ciphertext]):
    @staticmethod
    def uniformKey() -> Annotated[Key, Crypto.UniformlyRandom]: pass
    @staticmethod
    def uniformCiphertext() -> Annotated[Ciphertext, Crypto.UniformlyRandom]: pass
    @staticmethod
    def Encrypt(key: Key, msg: Message) -> Ciphertext: pass
    @staticmethod
    def Decrypt(key: Key, ctxt: Ciphertext) -> Message: pass

class INDCPA_Adversary(Crypto.Adversary, Generic[Key, Message, Ciphertext]):
    def run(self, o_eavesdrop: Callable[[Message, Message], Ciphertext]) -> Crypto.Bit: pass

class INDCPA_Left(Crypto.Game, Generic[Key, Message, Ciphertext]):
    def __init__(self, Scheme: Type[SymEncScheme[Key, Message, Ciphertext]], Adversary: Type[INDCPA_Adversary[Key, Message, Ciphertext]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.k = self.Scheme.uniformKey()
        r = self.adversary.run(self.o_eavesdrop)
        return r
    def o_eavesdrop(self, msg_L: Message, msg_R: Message) -> Ciphertext:
        c = self.Scheme.Encrypt(self.k, msg_L)
        return c

class INDCPA_Right(Crypto.Game, Generic[Key, Message, Ciphertext]):
    def __init__(self, Scheme: Type[SymEncScheme[Key, Message, Ciphertext]], Adversary: Type[INDCPA_Adversary[Key, Message, Ciphertext]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.k = self.Scheme.uniformKey()
        r = self.adversary.run(self.o_eavesdrop)
        return r
    def o_eavesdrop(self, msg_L: Message, msg_R: Message) -> Ciphertext:
        c = self.Scheme.Encrypt(self.k, msg_R)
        return c

INDCPA = Crypto.DistinguishingExperimentLeftOrRight("SymEnc", "INDCPA", INDCPA_Left, INDCPA_Right, INDCPA_Adversary)

class INDCPADollar_Adversary(Crypto.Adversary, Generic[Key, Message, Ciphertext]):
    def run(self, o_ctxt: Callable[[Message], Ciphertext]) -> Crypto.Bit: pass

class INDCPADollar_Real(Crypto.Game, Generic[Key, Message, Ciphertext]):
    def __init__(self, Scheme: Type[SymEncScheme[Key, Message, Ciphertext]], Adversary: Type[INDCPADollar_Adversary[Key, Message, Ciphertext]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.k = self.Scheme.uniformKey()
        r = self.adversary.run(self.o_ctxt)
        return r
    def o_ctxt(self, msg: Message) -> Ciphertext:
        c = self.Scheme.Encrypt(self.k, msg)
        return c

class INDCPADollar_Random(Crypto.Game, Generic[Key, Message, Ciphertext]):
    def __init__(self, Scheme: Type[SymEncScheme[Key, Message, Ciphertext]], Adversary: Type[INDCPADollar_Adversary[Key, Message, Ciphertext]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.k = self.Scheme.uniformKey()
        r = self.adversary.run(self.o_ctxt)
        return r
    def o_ctxt(self, msg: Message) -> Ciphertext:
        c = self.Scheme.uniformCiphertext()
        return c

INDCPADollar = Crypto.DistinguishingExperimentRealOrRandom("SymEnc", "INDCPADollar", INDCPADollar_Real, INDCPADollar_Random, INDCPADollar_Adversary)
