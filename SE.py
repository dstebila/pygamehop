from abc import ABC
from typing import Callable, Tuple, Union

import Crypto

class Ciphertext(ABC): pass
class SecretKey(ABC): pass
class Message(ABC): pass
class Reject(object): pass

class Scheme(ABC):
    def Encrypt(self, k: SecretKey, msg: Message) -> Ciphertext: pass
    def Decrypt(self, k: SecretKey, ct: Ciphertext) -> Union[Message, Reject]: pass

class INDCPA_adversary(ABC):
    def setkey(self) -> SecretKey: pass
    def challenge(self, enc_oracle: Callable[[Message], Ciphertext]) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext, enc_oracle: Callable[[Message], Ciphertext]) -> Crypto.Bit: pass

def INDCPA0(se: Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    k = adversary.setkey()
    enc_oracle = lambda m: se.Encrypt(k, m)
    (m0, m1) = adversary.challenge(enc_oracle)
    ct = se.Encrypt(k, m0)
    return adversary.guess(ct, enc_oracle)

def INDCPA1(se: Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    k = adversary.setkey()
    enc_oracle = lambda m: se.Encrypt(k, m)
    (m0, m1) = adversary.challenge(enc_oracle)
    ct = se.Encrypt(k, m1)
    return adversary.guess(ct, enc_oracle)

class INDCCA_adversary(ABC):
    def setkey(self) -> SecretKey: pass
    def challenge(self, enc_oracle: Callable[[Message], Ciphertext], dec_oracle: Callable[[Ciphertext], Union[Message, Reject]]) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext, enc_oracle: Callable[[Message], Ciphertext], dec_oracle: Callable[[Ciphertext], Union[Message, Reject]]) -> Crypto.Bit: pass

def INDCCA0(se: Scheme, adversary: INDCCA_adversary) -> Crypto.Bit:
    k = adversary.setkey()
    enc_oracle = lambda m: se.Encrypt(k, m)
    dec_oracle_phase1 = lambda ct: se.Decrypt(k, ct)
    (m0, m1) = adversary.challenge(enc_oracle, dec_oracle_phase1)
    ctstar = se.Encrypt(k, m0)
    dec_oracle_phase2 = lambda ct: se.Decrypt(k, ct) if ct != ctstar else Reject()
    return adversary.guess(ctstar, enc_oracle, dec_oracle_phase2)

def INDCCA1(se: Scheme, adversary: INDCCA_adversary) -> Crypto.Bit:
    k = adversary.setkey()
    enc_oracle = lambda m: se.Encrypt(k, m)
    dec_oracle_phase1 = lambda ct: se.Decrypt(k, ct)
    (m0, m1) = adversary.challenge(enc_oracle, dec_oracle_phase1)
    ctstar = se.Encrypt(k, m1)
    dec_oracle_phase2 = lambda ct: se.Decrypt(k, ct) if ct != ctstar else Reject()
    return adversary.guess(ctstar, enc_oracle, dec_oracle_phase2)
