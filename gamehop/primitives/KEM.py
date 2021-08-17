from typing import Tuple, Type, Union

from . import Crypto

class KEMScheme(Crypto.Scheme):
    class PublicKey(): pass
    class SecretKey(): pass
    class Ciphertext(): pass
    class SharedSecret(): pass
    @staticmethod
    def KeyGen() -> Tuple[PublicKey, SecretKey]: pass
    @staticmethod
    def Encaps(pk: PublicKey) -> Tuple[Ciphertext, SharedSecret]: pass
    @staticmethod
    def Decaps(sk: SecretKey, ct: Ciphertext) -> Union[SharedSecret, Crypto.Reject]: pass

class INDCPA_Adversary(Crypto.Adversary):
    @staticmethod
    def guess(Scheme: Type[KEMScheme], pk: KEMScheme.PublicKey, ct: KEMScheme.Ciphertext, ss: KEMScheme.SharedSecret) -> Crypto.Bit: pass

class INDCPA_Real(Crypto.Game):
    def __init__(self, Scheme: Type[KEMScheme], Adversary: Type[INDCPA_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        (ct, ss_real) = self.Scheme.Encaps(pk)
        r = self.Adversary.guess(self.Scheme, pk, ct, ss_real)
        return r

class INDCPA_Random(Crypto.Game):
    def __init__(self, Scheme: Type[KEMScheme], Adversary: Type[INDCPA_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        (ct, _) = self.Scheme.Encaps(pk)
        ss_rand = Crypto.UniformlySample(self.Scheme.SharedSecret)
        r = self.Adversary.guess(self.Scheme, pk, ct, ss_rand)
        return r

INDCPA = Crypto.DistinguishingExperimentRealOrRandom(INDCPA_Real, INDCPA_Random, INDCPA_Adversary)

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
