from typing import Generic, Optional, Sized, Tuple, TypeVar

from gamehop.primitives import Crypto
from gamehop.primitives.KDF import KDFScheme
from gamehop.primitives.KEM import KEMScheme
from gamehop.primitives.OTP import OTPScheme
from gamehop.primitives.PKE import PKEScheme

PK = TypeVar('PK')
SK = TypeVar('SK')
CT_KEM = TypeVar('CT_KEM')
CT_BODY = TypeVar('CT_BODY', bound=Sized)
SS = TypeVar('SS')
PT = TypeVar('PT', bound=Sized)

InnerKDF = KDFScheme[SS, CT_BODY]
InnerKEM = KEMScheme[PK, SK, CT_KEM, SS]
InnerOTP = OTPScheme[CT_BODY, PT, CT_BODY]

class PKEfromKEM(
    Generic[PK, SK, CT_KEM, CT_BODY, SS, PT],
    PKEScheme[PK, SK, Tuple[CT_KEM, CT_BODY], PT]
):
    @staticmethod
    def KeyGen():
        return InnerKEM.KeyGen()
    @staticmethod
    def Encrypt(pk, msg):
        (ct_kem, ss) = InnerKEM.Encaps(pk)
        mask = InnerKDF.Eval(ss, "label", len(msg))
        ct_body = InnerOTP.Encrypt(mask, msg)
        return (ct_kem, ct_body)
    @staticmethod
    def Decrypt(sk, ct):
        (ct_kem, ct_body) = ct
        ss = InnerKEM.Decaps(sk, ct_kem)
        if ss is None:
            retvalue: Optional[PT] = None
        else:
            mask = InnerKDF.Eval(ss, "label", len(ct_body))
            retvalue = InnerOTP.Decrypt(mask, ct_body)
        return retvalue
