from abc import ABC
from typing import cast, Tuple, Union

import Crypto
import KEM
import PKE
import KDF

class PublicKey(PKE.PublicKey):
    def __init__(self, pk: KEM.PublicKey):
        self.pk = pk
class SecretKey(PKE.SecretKey):
    def __init__(self, sk: KEM.SecretKey):
        self.sk = sk
class Ciphertext(PKE.Ciphertext):
    def __init__(self, ct1: KEM.Ciphertext, ct2: Crypto.ByteString):
        self.ct1 = ct1
        self.ct2 = ct2
class Message(PKE.Message):
    def __init__(self, msg: Crypto.ByteString):
        self.msg = msg

class Scheme(PKE.Scheme):
    def __init__(self, kem: KEM.Scheme, kdf: KDF.Scheme) -> None:
        self.kem = kem
        self.kdf = kdf
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]:
        (pk, sk) = self.kem.KeyGen()
        return (PublicKey(pk), SecretKey(sk))
    def Encrypt(self, pk: PKE.PublicKey, msg: PKE.Message) -> Ciphertext:
        (ct1, ss) = self.kem.Encaps(cast(PublicKey, pk).pk)
        mask = self.kdf.F(ss, "")
        ct2 = mask ^ cast(Crypto.ByteString, msg)
        return Ciphertext(ct1, ct2)
    def Decrypt(self, sk: PKE.SecretKey, ct: PKE.Ciphertext) -> Union[Message, PKE.Reject]:
        ss = self.kem.Decaps(cast(SecretKey, sk).sk, cast(Ciphertext, ct).ct1)
        if isinstance(ss, KEM.Reject): return PKE.Reject()
        mask = self.kdf.F(ss, "")
        msg = cast(Ciphertext, ct).ct2 ^ mask
        return Message(msg)
