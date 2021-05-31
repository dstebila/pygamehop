from typing import Tuple, Union, Generic, Set

from gamehop.primitives import Crypto, KEM, PKE
from gamehop.primitives.KEM import SharedSecret

KEMScheme = KEM.KEMScheme
PKEScheme = PKE.PKEScheme

class Scheme(KEMScheme):
    def __init__(self, pke: PKEScheme) -> None:
        self.pke = pke
    def KeyGen(self) -> Tuple[KEM.PublicKey, KEM.SecretKey]:
        return self.pke.KeyGen()
    def Encaps(self, pk: KEM.PublicKey) -> Tuple[KEM.Ciphertext, KEM.SharedSecret]:
        ss = Crypto.UniformlySample(SharedSecret)
        ct = self.pke.Encrypt(pk, ss)
        return (ct, ss)
    def Decaps(self, sk: KEM.SecretKey, ct: KEM.Ciphertext) -> Union[KEM.SharedSecret, Crypto.Reject]:
        ss = self.pke.Decrypt(sk, ct)
        if isinstance(ss, Crypto.Reject): return ss
        else: return ss
