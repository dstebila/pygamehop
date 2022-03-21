from typing import Annotated, Generic, Sized, TypeVar

from gamehop.primitives import Crypto
from gamehop.primitives.SymEnc import SymEncScheme

SK = TypeVar('SK')
MSG = TypeVar('MSG')
CT = TypeVar('CT')

InnerSymEnc = SymEncScheme[SK, MSG, CT]

class SE(
    Generic[SK, MSG, CT],
    SymEncScheme[SK, MSG, CT]
):
    @staticmethod
    def uniformKey() -> Annotated[SK, Crypto.UniformlyRandom]: return InnerSymEnc.uniformKey()
    @staticmethod
    def uniformCiphertext() -> Annotated[CT, Crypto.UniformlyRandom]: return InnerSymEnc.uniformCiphertext()
    @staticmethod
    def Encrypt(key, msg):
        return InnerSymEnc.Encrypt(key, msg)
    @staticmethod
    def Decrypt(key, ctxt):
        return InnerSymEnc.Decrypt(key, ctxt)
