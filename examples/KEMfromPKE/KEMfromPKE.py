from typing import cast, Tuple, Union

from gamehop.primitives import Crypto
from gamehop.primitives.KEM import KEMScheme
from gamehop.primitives.PKE import PKEScheme

class PKE1(PKEScheme): pass


class KEMfromPKE(KEMScheme):
    class PublicKey(KEMScheme.PublicKey): pass
    class SecretKey(KEMScheme.SecretKey): pass
    class Ciphertext(KEMScheme.Ciphertext): pass
    class SharedSecret(KEMScheme.SharedSecret): pass
    @staticmethod
    def KeyGen() -> Tuple[PublicKey, SecretKey]:
        (pk, sk) = PKE1.KeyGen()
        pkprime = cast(KEMfromPKE.PublicKey, pk)
        skprime = cast(KEMfromPKE.SecretKey, sk)
        return (pkprime, skprime)
    @staticmethod
    def Encaps(pk: PublicKey) -> Tuple[Ciphertext, SharedSecret]: # type: ignore[override]
        ss = Crypto.UniformlySample(KEMfromPKE.SharedSecret)
        msgprime = cast(PKE1.Message, ss)
        pkprime = cast(PKE1.PublicKey, pk)
        ctprime = PKE1.Encrypt(pkprime, msgprime)
        ct = cast(KEMfromPKE.Ciphertext, ctprime)
        return (ct, ss)
    @staticmethod
    def Decaps(sk: SecretKey, ct: Ciphertext) -> Union[SharedSecret, Crypto.Reject]: # type: ignore[override]
        ctprime = cast(PKE1.Ciphertext, ct)
        skprime = cast(PKE1.SecretKey, sk)
        msgprime = PKE1.Decrypt(skprime, ctprime)
        if isinstance(msgprime, Crypto.Reject):
            r: Union[KEMfromPKE.SharedSecret, Crypto.Reject] = Crypto.Reject()
        else:
            r = cast(KEMfromPKE.SharedSecret, msgprime)
        return r
