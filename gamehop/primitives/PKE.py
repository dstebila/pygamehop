from typing import Callable, Generic, Optional, Sized, Tuple, Type, TypeVar

from . import Crypto

PublicKey = TypeVar('PublicKey')
SecretKey = TypeVar('SecretKey')
Ciphertext = TypeVar('Ciphertext')
Message = TypeVar('Message', bound=Sized)

class PKEScheme(Crypto.Scheme, Generic[PublicKey, SecretKey, Ciphertext, Message]):
    @staticmethod
    def KeyGen() -> Tuple[PublicKey, SecretKey]: pass
    @staticmethod
    def Encrypt(pk: PublicKey, msg: Message) -> Ciphertext: pass
    @staticmethod
    def Decrypt(sk: SecretKey, ct: Ciphertext) -> Optional[Message]: pass

class INDCPA_Adversary(Crypto.Adversary, Generic[PublicKey, SecretKey, Ciphertext, Message]):
    def challenge(self, pk: PublicKey) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext) -> Crypto.Bit: pass

class INDCPA_Left(Crypto.Game, Generic[PublicKey, SecretKey, Ciphertext, Message]):
    def __init__(self, Scheme: Type[PKEScheme[PublicKey, SecretKey, Ciphertext, Message]], Adversary: Type[INDCPA_Adversary[PublicKey, SecretKey, Ciphertext, Message]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        (m0, m1) = self.adversary.challenge(pk)
        ct = self.Scheme.Encrypt(pk, m0)
        r = self.adversary.guess(ct)
        if len(m0) == len(m1): ret = r
        else: ret = Crypto.Bit(0)
        return ret

class INDCPA_Right(Crypto.Game, Generic[PublicKey, SecretKey, Ciphertext, Message]):
    def __init__(self, Scheme: Type[PKEScheme[PublicKey, SecretKey, Ciphertext, Message]], Adversary: Type[INDCPA_Adversary[PublicKey, SecretKey, Ciphertext, Message]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        (m0, m1) = self.adversary.challenge(pk)
        ct = self.Scheme.Encrypt(pk, m1)
        r = self.adversary.guess(ct)
        if len(m0) == len(m1): ret = r
        else: ret = Crypto.Bit(0)
        return ret

INDCPA = Crypto.DistinguishingExperimentLeftOrRight("PKE", "INDCPA", INDCPA_Left, INDCPA_Right, INDCPA_Adversary)

class INDCCA2_Adversary(Crypto.Adversary, Generic[PublicKey, SecretKey, Ciphertext, Message]):
    def challenge(self, pk: PublicKey, o_decrypt: Callable[[Ciphertext], Optional[Message]]) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext, o_decrypt: Callable[[Ciphertext], Optional[Message]]) -> Crypto.Bit: pass

class INDCCA2_Left(Crypto.Game, Generic[PublicKey, SecretKey, Ciphertext, Message]):
    def __init__(self, Scheme: Type[PKEScheme[PublicKey, SecretKey, Ciphertext, Message]], Adversary: Type[INDCCA2_Adversary[PublicKey, SecretKey, Ciphertext, Message]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        self.sk = sk
        self.ctstar = None
        (m0, m1) = self.adversary.challenge(pk, self.o_decrypt)
        self.ctstar = self.Scheme.Encrypt(pk, m0)
        r = self.adversary.guess(self.ctstar, self.o_decrypt)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret
    def o_decrypt(self, ct: Ciphertext) -> Optional[Message]:
        ret: Optional[Message] = None
        if ct != self.ctstar: ret = self.Scheme.Decrypt(self.sk, ct)
        return ret

class INDCCA2_Right(Crypto.Game, Generic[PublicKey, SecretKey, Ciphertext, Message]):
    def __init__(self, Scheme: Type[PKEScheme[PublicKey, SecretKey, Ciphertext, Message]], Adversary: Type[INDCCA2_Adversary[PublicKey, SecretKey, Ciphertext, Message]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        self.sk = sk
        self.ctstar = None
        (m0, m1) = self.adversary.challenge(pk, self.o_decrypt)
        self.ctstar = self.Scheme.Encrypt(pk, m1)
        r = self.adversary.guess(self.ctstar, self.o_decrypt)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret
    def o_decrypt(self, ct: Ciphertext) -> Optional[Message]:
        ret: Optional[Message] = None
        if ct != self.ctstar: ret = self.Scheme.Decrypt(self.sk, ct)
        return ret

INDCCA2 = Crypto.DistinguishingExperimentLeftOrRight("PKE", "INDCCA2", INDCCA2_Left, INDCCA2_Right, INDCCA2_Adversary)
