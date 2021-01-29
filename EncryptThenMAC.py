from abc import ABC
from typing import cast, Tuple, Union

import Crypto
import SE
import MAC

class SecretKey(SE.SecretKey):
    def __init__(self, sk_enc: SE.SecretKey, sk_mac: MAC.SecretKey):
        self.sk_enc = sk_enc
        self.sk_mac = sk_mac
class Ciphertext(SE.Ciphertext):
    def __init__(self, ct: SE.Ciphertext, tag: MAC.Tag):
        self.ct = ct
        self.tag = tag

class Scheme(SE.Scheme):
    def __init__(self, se: SE.Scheme, mac: MAC.Scheme) -> None:
        self.se = se
        self.mac = mac
    def Encrypt(self, k: SecretKey, msg: SE.Message) -> Ciphertext: # type: ignore[override]
        ct = self.se.Encrypt(k.sk_enc, msg)
        tag = self.mac.MAC(k.sk_mac, cast(MAC.Message, ct))
        return Ciphertext(ct, tag)
    def Decrypt(self, k: SecretKey, ct: Ciphertext) -> Union[SE.Message, SE.Reject]: # type: ignore[override]
        tagprime = self.mac.MAC(k.sk_mac, cast(MAC.Message, ct.ct))
        if tagprime != ct.tag: return SE.Reject()
        msg = self.se.Decrypt(k.sk_enc, ct.ct)
        if isinstance(msg, SE.Reject): return msg
        else: return msg
