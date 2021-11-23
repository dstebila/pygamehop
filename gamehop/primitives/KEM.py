from typing import Annotated, Generic, Optional, Tuple, Type, TypeVar

from . import Crypto

PublicKey = TypeVar('PublicKey')
SecretKey = TypeVar('SecretKey')
Ciphertext = TypeVar('Ciphertext')
SharedSecret = TypeVar('SharedSecret')

class KEMScheme(Crypto.Scheme, Generic[PublicKey, SecretKey, Ciphertext, SharedSecret]):
    @staticmethod
    def uniformSharedSecret() -> Annotated[SharedSecret, Crypto.UniformlyRandom]: pass
    @staticmethod
    def KeyGen() -> Tuple[PublicKey, SecretKey]: pass
    @staticmethod
    def Encaps(pk: PublicKey) -> Tuple[Ciphertext, SharedSecret]: pass
    @staticmethod
    def Decaps(sk: SecretKey, ct: Ciphertext) -> Optional[SharedSecret]: pass

class INDCPA_Adversary(Crypto.Adversary, Generic[PublicKey, SecretKey, Ciphertext, SharedSecret]):
    def guess(self, pk: PublicKey, ct: Ciphertext, ss: SharedSecret) -> Crypto.Bit: pass

class INDCPA_Real(Crypto.Game, Generic[PublicKey, SecretKey, Ciphertext, SharedSecret]):
    def __init__(self, Scheme: Type[KEMScheme[PublicKey, SecretKey, Ciphertext, SharedSecret]], Adversary: Type[INDCPA_Adversary[PublicKey, SecretKey, Ciphertext, SharedSecret]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        (ct, ss_real) = self.Scheme.Encaps(pk)
        r = self.adversary.guess(pk, ct, ss_real)
        return r

class INDCPA_Random(Crypto.Game, Generic[PublicKey, SecretKey, Ciphertext, SharedSecret]):
    def __init__(self, Scheme: Type[KEMScheme[PublicKey, SecretKey, Ciphertext, SharedSecret]], Adversary: Type[INDCPA_Adversary[PublicKey, SecretKey, Ciphertext, SharedSecret]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        (ct, _) = self.Scheme.Encaps(pk)
        ss_rand = self.Scheme.uniformSharedSecret()
        r = self.adversary.guess(pk, ct, ss_rand)
        return r

INDCPA = Crypto.DistinguishingExperimentRealOrRandom("KEM.INDCPA", INDCPA_Real, INDCPA_Random, INDCPA_Adversary)

# an alternative formulation of INDCPA using a hidden bit
# class INDCPA_HiddenBit(Crypto.Game):
#     def main(self, kem: KEMScheme, Adversary: Type[INDCPA_Adversary], b: Crypto.Bit) -> Crypto.Bit:
#         adversary = Adversary(kem)
#         (pk, sk) = kem.KeyGen()
#         (ct, ss_real) = kem.Encaps(pk)
#         ss_rand = Crypto.UniformlySample(SharedSecret)
#         ss_challenge = ss_real if b == 0 else ss_rand
#         return adversary.guess(pk, ct, ss_challenge)
# 
# INDCPAv2 = Crypto.DistinguishingExperimentHiddenBit(INDCPA_HiddenBit, INDCPA_Adversary)
