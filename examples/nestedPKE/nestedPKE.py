from typing import cast, Tuple, Union

from gamehop.primitives import Crypto
from gamehop.primitives.PKE import PKEScheme

class PKE1(PKEScheme): pass
class PKE2(PKEScheme): pass

class NestedPKE(PKEScheme):
    class PublicKey(PKEScheme.PublicKey):
        def __init__(self, pk1: PKE1.PublicKey, pk2: PKE2.PublicKey):
            self.pk1 = pk1
            self.pk2 = pk2
    class SecretKey(PKEScheme.SecretKey):
        def __init__(self, sk1: PKE1.SecretKey, sk2: PKE2.SecretKey):
            self.sk1 = sk1
            self.sk2 = sk2
    class Ciphertext(PKEScheme.Ciphertext): pass
    class Message(PKEScheme.Message): pass
    @staticmethod
    def KeyGen() -> Tuple[PublicKey, SecretKey]:
        (pk1, sk1) = PKE1.KeyGen()
        (pk2, sk2) = PKE2.KeyGen()
        pkprime = NestedPKE.PublicKey(pk1, pk2)
        skprime = NestedPKE.SecretKey(sk1, sk2)
        return (pkprime, skprime)
    @staticmethod
    def Encrypt(pk: PublicKey, msg: Message) -> Ciphertext: # type: ignore[override]
        ct1 = PKE1.Encrypt(pk.pk1, msg)
        pt2 = cast(PKE2.Message, ct1)
        ct2 = PKE2.Encrypt(pk.pk2, pt2)
        ctprime = cast(NestedPKE.Ciphertext, ct2)
        return ctprime
    @staticmethod
    def Decrypt(sk: SecretKey, ct: Ciphertext) -> Union[Crypto.Reject, Message]: # type: ignore[override]
        pt2 = PKE2.Decrypt(sk.sk2, ct)
        if pt2 == Crypto.Reject:
            r: Union[Crypto.Reject, NestedPKE.Message] = Crypto.Reject()
        else:
            ct1 = cast(PKE1.Ciphertext, pt2)
            pt1 = PKE1.Decrypt(sk.sk1, ct1)
            r = cast(NestedPKE.Message, pt1)
        return r
