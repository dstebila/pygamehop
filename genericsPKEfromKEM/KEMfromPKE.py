from typing import Tuple, Union, Generic

import Crypto
import KEM
import PKE

SharedSecretKey = Crypto.SharedSecretKey
KEM_Scheme = KEM.Scheme[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext, Crypto.Reject]

class Scheme(Generic[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext], KEM_Scheme):
    def __init__(self, pke: PKE.Scheme) -> None:
        self.pke = pke
    def KeyGen(self) -> Tuple[PKE.PublicKey, PKE.SecretKey]:
        return self.pke.KeyGen()
    def Encaps(self, pk: PKE.PublicKey) -> Tuple[PKE.Ciphertext, SharedSecretKey]:
        ss = SharedSecretKey()
        ct = self.pke.Encrypt(pk, ss)
        return (ct, ss)
    def Decaps(self, sk: PKE.SecretKey, ct: PKE.Ciphertext) -> Union[SharedSecretKey, Crypto.Reject]:
        ss = self.pke.Decrypt(sk, ct)
        if isinstance(ss, Crypto.Reject): return ss
        else: return ss
