from abc import ABC
from typing import Callable

import Crypto

class SecretKey(ABC): pass
class Tag(ABC): pass
class Message(ABC): pass

class Scheme(ABC):
    @staticmethod
    def MAC(k: SecretKey, m: Message) -> Tag: pass

class EUFCMA_adversary(ABC):
    def setkey(self) -> SecretKey: pass
    def guess(self, mac_oracle: Callable[[Message], Tag], verify_oracle: Callable[[Message, Tag], bool]): pass

def EUFCMA_real(mac: Scheme, adversary: EUFCMA_adversary) -> Crypto.Bit:
    k = adversary.setkey()
    mac_oracle = lambda m: mac.MAC(k, m)
    verify_oracle = lambda m, t: t == mac.MAC(k, m)
    return adversary.guess(mac_oracle, verify_oracle)

def EUFCMA_ideal(mac: Scheme, adversary: EUFCMA_adversary) -> Crypto.Bit:
    k = adversary.setkey()
    messages_maced = set()
    def mac_oracle(m: Message) -> Tag:
        t = mac.MAC(k, m)
        messages_maced.add((m, t))
        return t
    verify_oracle = lambda m, t: (m, t) in messages_maced
    return adversary.guess(mac_oracle, verify_oracle)
