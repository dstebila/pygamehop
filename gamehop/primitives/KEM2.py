from typing import Tuple, Union, Generic, Set

from . import Crypto
from .. import proofs

class PublicKey(): pass
class SecretKey(): pass
class Ciphertext(): pass
class SharedSecret(): pass

class KEMScheme(Crypto.Scheme):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encaps(self, pk: PublicKey) -> Tuple[Ciphertext, SharedSecret]: pass
    def Decaps(self, sk: SecretKey, ct: Ciphertext) -> Union[SharedSecret, Crypto.Reject]: pass

class KEMINDCPA_adversary(Crypto.Adversary):
    def setup(self, kem: KEMScheme): pass
    def guess(self, pk: PublicKey, ct: Ciphertext, ss: SharedSecret) -> Crypto.Bit: pass

class INDCPA(proofs.GuessingExperiment):
    def main(self, kem: KEMScheme, adversary: KEMINDCPA_adversary, b: Crypto.Bit) -> Crypto.Bit:
        dummy = adversary.setup(kem)
        (pk, sk) = kem.KeyGen()
        (ct, ss_real) = kem.Encaps(pk)
        ss_rand = Crypto.UniformlySample(SharedSecret)
        ss_challenge = ss_real if b == 0 else ss_rand
        # alternatively:
        # ss_challenge = (1 - b) * ss_real + (b * ss_rand)
        return adversary.guess(pk, ct, ss_challenge)
