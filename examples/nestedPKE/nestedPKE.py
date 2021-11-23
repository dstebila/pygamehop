from typing import cast, Generic, Optional, Sized, Tuple, TypeVar

from gamehop.primitives import Crypto
from gamehop.primitives.PKE import PKEScheme

PK1 = TypeVar('PK1')
SK1 = TypeVar('SK1')
CT1 = TypeVar('CT1', bound=Sized)
PT1 = TypeVar('PT1', bound=Sized)
PK2 = TypeVar('PK2')
SK2 = TypeVar('SK2')
CT2 = TypeVar('CT2')
# Missing PT2 since PT2 will be the same as CT1

PKE1 = PKEScheme[PK1, SK1, CT1, PT1]
PKE2 = PKEScheme[PK2, SK2, CT2, CT1]

class NestedPKE(
    Generic[PK1, PK2, SK1, SK2, CT1, CT2, PT1],
    PKEScheme[Tuple[PK1, PK2], Tuple[SK1, SK2], CT2, PT1]
):
    @staticmethod
    def KeyGen():
        (pk1, sk1) = PKE1.KeyGen()
        (pk2, sk2) = PKE2.KeyGen()
        return ((pk1, pk2), (sk1, sk2))
    @staticmethod
    def Encrypt(npk, msg):
        (pk1, pk2) = npk
        ct1 = PKE1.Encrypt(pk1, msg)
        ct2 = PKE2.Encrypt(pk2, ct1)
        return ct2
    @staticmethod
    def Decrypt(nsk, ct2):
        (sk1, sk2) = nsk
        pt2 = PKE2.Decrypt(sk2, ct2)
        if pt2 == None:
            r: Optional[PT1] = None
        else:
            r = PKE1.Decrypt(sk1, pt2)
        return r
