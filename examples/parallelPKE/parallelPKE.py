from typing import cast, Generic, Optional, Sized, Tuple, TypeVar

from gamehop.primitives import Crypto
from gamehop.primitives.PKE import PKEScheme

PK1 = TypeVar('PK1')
SK1 = TypeVar('SK1')
CT1 = TypeVar('CT1')
PK2 = TypeVar('PK2')
SK2 = TypeVar('SK2')
CT2 = TypeVar('CT2')
PT12 = TypeVar('PT12', bound=Sized) # Use the same plaintext space for both schemes

PKE1 = PKEScheme[PK1, SK1, CT1, PT12]
PKE2 = PKEScheme[PK2, SK2, CT2, PT12]

class ParallelPKE(
    Generic[PK1, PK2, SK1, SK2, CT1, CT2, PT12],
    PKEScheme[Tuple[PK1, PK2], Tuple[SK1, SK2], Tuple[CT1, CT2], PT12]):
    @staticmethod
    def KeyGen():
        (pk1, sk1) = PKE1.KeyGen()
        (pk2, sk2) = PKE2.KeyGen()
        return ((pk1, pk2), (sk1, sk2))
    @staticmethod
    def Encrypt(npk, msg):
        (pk1, pk2) = npk
        ct1 = PKE1.Encrypt(pk1, msg)
        ct2 = PKE2.Encrypt(pk2, msg)
        return (ct1, ct2)
    @staticmethod
    def Decrypt(nsk, nct):
        (sk1, sk2) = nsk
        (ct1, ct2) = nct
        pt1 = PKE1.Decrypt(sk1, ct1)
        pt2 = PKE2.Decrypt(sk2, ct2)
        if pt1 is None or pt2 is None or pt1 != pt2:
            r: Optional[PT12] = None
        else:
            r = pt1
        return r
