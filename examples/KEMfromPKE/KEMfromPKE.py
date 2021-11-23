from typing import Annotated, Generic, TypeVar

from gamehop.primitives import Crypto
from gamehop.primitives.KEM import KEMScheme
from gamehop.primitives.PKE import PKEScheme

PK = TypeVar('PK')
SK = TypeVar('SK')
CT = TypeVar('CT')
SS = TypeVar('SS')

InnerPKE = PKEScheme[PK, SK, CT, SS]

class KEMfromPKE(
    Generic[PK, SK, CT, SS],
    KEMScheme[PK, SK, CT, SS]
):
    @staticmethod
    def uniformSharedSecret() -> Annotated[SS, Crypto.UniformlyRandom]: return KEMfromPKE.uniformSharedSecret()
    @staticmethod
    def KeyGen():
        return InnerPKE.KeyGen()
    @staticmethod
    def Encaps(pk):
        ss = KEMfromPKE.uniformSharedSecret()
        ct = InnerPKE.Encrypt(pk, ss)
        return (ct, ss)
    @staticmethod
    def Decaps(sk, ct):
        return InnerPKE.Decrypt(sk, ct)
