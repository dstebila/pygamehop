from typing import cast, Tuple, Union

from gamehop.primitives import Crypto
from gamehop.primitives.PKE import PKEScheme

class PKE1(PKEScheme): pass
class PKE2(PKEScheme): pass

class ParallelPKE(PKEScheme):
    class PublicKey(PKEScheme.PublicKey):
        def __init__(self, pk1: PKE1.PublicKey, pk2: PKE2.PublicKey):
            self.pk1 = pk1
            self.pk2 = pk2
    class SecretKey(PKEScheme.SecretKey):
        def __init__(self, sk1: PKE1.SecretKey, sk2: PKE2.SecretKey):
            self.sk1 = sk1
            self.sk2 = sk2
    class Ciphertext(PKEScheme.Ciphertext):
        def __init__(self, ct1: PKE1.Ciphertext, ct2: PKE2.Ciphertext):
            self.ct1 = ct1
            self.ct2 = ct2
    class Message(PKEScheme.Message): pass

    @staticmethod
    def KeyGen() -> Tuple[PublicKey, SecretKey]:
        (pk1, sk1) = PKE1.KeyGen()
        (pk2, sk2) = PKE2.KeyGen()
        pkprime = ParallelPKE.PublicKey(pk1, pk2)
        skprime = ParallelPKE.SecretKey(sk1, sk2)
        return (pkprime, skprime)
    @staticmethod
    def Encrypt(pk: PublicKey, msg: Message) -> Ciphertext: # type: ignore[override]
        ct1 = PKE1.Encrypt(pk.pk1, msg)
        ct2 = PKE2.Encrypt(pk.pk2, msg)
        ct = ParallelPKE.Ciphertext(ct1, ct2)
        return ct
    @staticmethod
    def Decrypt(sk: SecretKey, ct: Ciphertext) -> Union[Crypto.Reject, Message]: # type: ignore[override]
        pt1 = PKE1.Decrypt(sk.sk1, ct.ct1)
        pt2 = PKE2.Decrypt(sk.sk2, ct.ct2)
        if pt1 == Crypto.Reject or pt1 == Crypto.Reject or pt1 != pt2:
            r = Crypto.Reject
        else:
            r = cast(Message, pt1)
        return r
