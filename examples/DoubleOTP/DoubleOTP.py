from typing import Generic, Optional, Sized, Tuple, TypeVar

from gamehop.primitives import Crypto
from gamehop.primitives.OTP import OTPScheme

SK1 = TypeVar('SK1')
CT1 = TypeVar('CT1', bound=Sized)
PT1 = TypeVar('PT1', bound=Sized)
SK2 = TypeVar('SK2')
CT2 = TypeVar('CT2', bound=Sized)
# Missing PT2 since PT2 will be the same as CT1

InnerOTP = OTPScheme[SK1, PT1, CT1]
OuterOTP = OTPScheme[SK2, CT1, CT2]

class DoubleOTP(
    Generic[SK1, SK2, CT1, CT2, PT1],
    OTPScheme[Tuple[SK1, SK2], PT1, CT2]
):
    @staticmethod
    def KeyGen(keylen):
        sk1 = InnerOTP.KeyGen(keylen)
        sk2 = OuterOTP.KeyGen(keylen)
        dsk = (sk1, sk2)
        return dsk
    @staticmethod
    def Encrypt(dsk, msg):
        (sk1, sk2) = dsk
        ct1 = InnerOTP.Encrypt(sk1, msg)
        ct2 = OuterOTP.Encrypt(sk2, ct1)
        return ct2
    @staticmethod
    def Decrypt(dsk, ct2):
        (sk1, sk2) = dsk
        pt2 = OuterOTP.Decrypt(sk2, ct2)
        pt1 = InnerOTP.Decrypt(sk1, pt2)
        return pt1
