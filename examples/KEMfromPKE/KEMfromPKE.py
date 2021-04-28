from typing import Tuple, Union, Generic, Set

from gamehop.primitives import Crypto, KEM, PKE

KEMScheme = KEM.KEMScheme
PKEScheme = PKE.PKEScheme

class Scheme(KEMScheme):
    def __init__(self, pke: PKEScheme) -> None:
        self.pke = pke
        self.SharedSecretSet = self.pke.MessageSet
    def KeyGen(self) -> Tuple[PKEScheme.PublicKey, PKEScheme.SecretKey]:
        return self.pke.KeyGen()
    def Encaps(self, pk: PKEScheme.PublicKey) -> Tuple[PKEScheme.Ciphertext, PKEScheme.Message]:
        ss = Crypto.UniformlySample(self.pke.MessageSet)
        ct = self.pke.Encrypt(pk, ss)
        return (ct, ss)
    def Decaps(self, sk: PKEScheme.SecretKey, ct: PKEScheme.Ciphertext) -> Union[PKEScheme.Message, Crypto.Reject]:
        ss = self.pke.Decrypt(sk, ct)
        if isinstance(ss, Crypto.Reject): return ss
        else: return ss
