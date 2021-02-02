from abc import ABC
from typing import cast, Tuple, Union

import Crypto
import KEM
import PKE

class PublicKey(KEM.PublicKey):
    def __init__(self, pk: PKE.PublicKey):
        self.pk = pk
class SecretKey(KEM.SecretKey):
    def __init__(self, sk: PKE.SecretKey):
        self.sk = sk
class Ciphertext(KEM.Ciphertext):
    def __init__(self, ct: PKE.Ciphertext):
        self.ct = ct
class SharedSecret(KEM.SharedSecret):
    def __init__(self, ss: Crypto.ByteString):
        self.ss = ss

class Scheme(KEM.Scheme):
    def __init__(self, pke: PKE.Scheme) -> None:
        self.pke = pke
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]:
        (pk, sk) = self.pke.KeyGen()
        return (PublicKey(pk), SecretKey(sk))
    def Encaps(self, pk: KEM.PublicKey) -> Tuple[Ciphertext, SharedSecret]:
        ss = Crypto.UniformlyRandomByteString()
        ct = self.pke.Encrypt(cast(PublicKey, pk).pk, cast(PKE.Message, ss))
        return (Ciphertext(ct), SharedSecret(ss))
    def Decaps(self, sk: KEM.SecretKey, ct: KEM.Ciphertext) -> Union[SharedSecret, KEM.Reject]:
        ss = self.pke.Decrypt(cast(SecretKey, sk).sk, cast(Ciphertext, ct).ct)
        if isinstance(ss, KEM.Reject): return ss
        else: return SharedSecret(cast(Crypto.ByteString, ss))
