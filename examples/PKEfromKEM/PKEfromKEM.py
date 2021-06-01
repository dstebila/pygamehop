from typing import Tuple, Union, Generic, Set

from gamehop.primitives import Crypto, KEM, PKE, KDF

KEMScheme = KEM.KEMScheme
KDFScheme = KDF.KDFScheme

class Scheme(PKE.PKEScheme):
    def __init__(self, kem: KEMScheme, kdf: KDFScheme) -> None:
        self.kem = kem
        self.kdf = kdf
    def KeyGen(self) -> Tuple[PKE.PublicKey, PKE.SecretKey]:
        return self.kem.KeyGen()
    def Encrypt(self, pk: PKE.PublicKey, msg: PKE.Message) -> PKE.Ciphertext:
        (ct1, ss) = self.kem.Encaps(pk)
        mask = self.kdf.KDF(ss, "label", len(msg))
        ct2 = mask ^ msg
        return (ct1, ct2)
    def Decrypt(self, sk: PKE.SecretKey, ct: PKE.Ciphertext) -> Tuple[PKE.Message, Crypto.Reject]:
        (ct1, ct2) = ct
        ss = self.kem.Decaps(sk, ct1)
        mask = self.kdf.KDF(ss, "label", len(ct2))
        msg = ct2 ^ mask
        retvalue = Crypto.Reject() if isinstance(ss, Crypto.Reject) else msg
        return msg
