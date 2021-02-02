from typing import Tuple, Union, Generic, Set

import Crypto
import KEM
import PKE



KEM_Scheme = KEM.Scheme[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext, PKE.Message, Crypto.Reject]

class Scheme(Generic[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext, PKE.Message], KEM_Scheme):
    def __init__(self, pke: PKE.Scheme) -> None:
        self.pke = pke
        self.SharedSecretSet = self.pke.MessageSet
    def KeyGen(self) -> Tuple[PKE.PublicKey, PKE.SecretKey]:
        return self.pke.KeyGen()
    def Encaps(self, pk: PKE.PublicKey) -> Tuple[PKE.Ciphertext, PKE.Message]:
        ss = Crypto.UniformlySample(self.pke.MessageSet)
        ct = self.pke.Encrypt(pk, ss)
        return (ct, ss)
    def Decaps(self, sk: PKE.SecretKey, ct: PKE.Ciphertext) -> Union[PKE.Message, Crypto.Reject]:
        ss = self.pke.Decrypt(sk, ct)
        if isinstance(ss, Crypto.Reject): return ss
        else: return ss
