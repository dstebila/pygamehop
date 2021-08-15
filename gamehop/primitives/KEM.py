from typing import Tuple, Type, Union

from . import Crypto

class PublicKey(): pass
class SecretKey(): pass
class Ciphertext(): pass
class SharedSecret(): pass

class KEM(Crypto.Scheme):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encaps(self, pk: PublicKey) -> Tuple[Ciphertext, SharedSecret]: pass
    def Decaps(self, sk: SecretKey, ct: Ciphertext) -> Union[SharedSecret, Crypto.Reject]: pass

class INDCPA_Adversary(Crypto.Adversary):
    def __init__(self, kem: KEM): pass
    def guess(self, pk: PublicKey, ct: Ciphertext, ss: SharedSecret) -> Crypto.Bit: pass

class INDCPA_Real(Crypto.Game):
    def main(self, kem: KEM, Adversary: Type[INDCPA_Adversary]) -> Crypto.Bit:
        adversary = Adversary(kem)
        (pk, sk) = kem.KeyGen()
        (ct, ss_real) = kem.Encaps(pk)
        r = adversary.guess(pk, ct, ss_real)
        return r

class INDCPA_Random(Crypto.Game):
    def main(self, kem: KEM, Adversary: Type[INDCPA_Adversary]) -> Crypto.Bit:
        adversary = Adversary(kem)
        (pk, sk) = kem.KeyGen()
        (ct, _) = kem.Encaps(pk)
        ss_rand = Crypto.UniformlySample(SharedSecret)
        r = adversary.guess(pk, ct, ss_rand)
        return r

INDCPA = Crypto.DistinguishingExperimentRealOrRandom(INDCPA_Real, INDCPA_Random, INDCPA_Adversary)

# an alternative formulation of INDCPA using a hidden bit
class INDCPA_HiddenBit(Crypto.Game):
    def main(self, kem: KEM, Adversary: Type[INDCPA_Adversary], b: Crypto.Bit) -> Crypto.Bit:
        adversary = Adversary(kem)
        (pk, sk) = kem.KeyGen()
        (ct, ss_real) = kem.Encaps(pk)
        ss_rand = Crypto.UniformlySample(SharedSecret)
        ss_challenge = ss_real if b == 0 else ss_rand
        return adversary.guess(pk, ct, ss_challenge)

INDCPAv2 = Crypto.DistinguishingExperimentHiddenBit(INDCPA_HiddenBit, INDCPA_Adversary)
