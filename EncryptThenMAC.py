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
    def Encrypt(self, k: SE.SecretKey, msg: SE.Message) -> Ciphertext:
        ct = self.se.Encrypt(cast(SecretKey, k).sk_enc, msg)
        tag = self.mac.MAC(cast(SecretKey, k).sk_mac, cast(MAC.Message, ct))
        return Ciphertext(ct, tag)
    def Decrypt(self, k: SE.SecretKey, ct_in: SE.Ciphertext) -> Union[SE.Message, SE.Reject]:
        tagprime = self.mac.MAC(cast(SecretKey, k).sk_mac, cast(MAC.Message, cast(Ciphertext, ct_in).ct))
        if tagprime != cast(Ciphertext, ct_in).tag: return SE.Reject()
        msg = self.se.Decrypt(cast(SecretKey, k).sk_enc, cast(Ciphertext, ct_in).ct)
        if isinstance(msg, SE.Reject): return msg
        else: return msg
