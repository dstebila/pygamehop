from typing import Annotated, Generic, Tuple, TypeVar

from gamehop.primitives import Crypto
from gamehop.primitives.SymEnc import SymEncScheme
from gamehop.primitives.MAC import MACScheme

SEK = TypeVar('SEK')
MSG = TypeVar('MSG')
CT = TypeVar('CT')
MACK = TypeVar('MACK')
TAG = TypeVar('TAG')

InnerSymEnc = SymEncScheme[SEK, MSG, CT]
InnerMAC = MACScheme[MACK, CT, TAG]

class EncryptThenMAC(
    Generic[SEK, MSG, CT, MACK, TAG],
    SymEncScheme[Tuple[SEK, MACK], MSG, Tuple[CT, TAG]]
):
    @staticmethod
    def uniformKey(): 
        sek = InnerSymEnc.uniformKey()
        mack = InnerMAC.uniformKey()
        return (sek, mack)
    @staticmethod
    def uniformCiphertext(): pass
    @staticmethod
    def Encrypt(key, msg):
        (sek, mack) = key
        ct = InnerSymEnc.Encrypt(sek, msg)
        tag = InnerMAC.MAC(mack, ct)
        return (ct, tag)
    @staticmethod
    def Decrypt(key, ctxt):
        (sek, mack) = key
        (ct, tag) = ctxt
        if InnerMAC.MAC(mack, ct) != tag: ret = None
        else: ret = InnerSymEnc.Decrypt(sek, ct)
        return ret
