from typing import Tuple, Union, Generic

import Crypto
import KEM
import PKE

class Scheme(Generic[PKE.Message, PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext], KEM.Scheme[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext, Crypto.ByteString, Crypto.Reject]):
    def __init__(self, pke: PKE.Scheme) -> None:
        self.pke = pke
    def KeyGen(self) -> Tuple[PKE.PublicKey, PKE.SecretKey]:
        return self.pke.KeyGen()

    def Encaps(self, pk: PKE.PublicKey) -> Tuple[PKE.Ciphertext, Crypto.ByteString]:
        ss = Crypto.UniformlyRandomByteString()
        ct = self.pke.Encrypt(pk, self.pke.ByteStringToMessage(ss))
        return (ct, ss)
    def Decaps(self, sk: PKE.SecretKey, ct: PKE.Ciphertext) -> Union[Crypto.ByteString, Crypto.Reject]:
        ss = self.pke.Decrypt(sk, ct)
        if isinstance(ss, Crypto.Reject): return ss
        else: return self.pke.MessageToByteString(ss)
