from abc import ABC
from typing import Tuple, Union, TypeVar, Generic

import Crypto

Ciphertext = TypeVar('Ciphertext')
PublicKey = TypeVar('PublicKey')
SecretKey = TypeVar('SecretKey')
Message = TypeVar('Message')
Reject = TypeVar('Reject')

class Scheme(Generic[Ciphertext, PublicKey, SecretKey, Message, Reject]):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encrypt(self, pk: PublicKey, msg: Message) -> Ciphertext: pass
    def Decrypt(self, sk: SecretKey, ct: Ciphertext) -> Union[Message, Reject]: pass
    def ByteStringToMessage(self, s: Crypto.ByteString) -> Message: pass
    def MessageToByteString(self, m: Message) -> Crypto.ByteString: pass

class INDCPA_adversary(Generic[Ciphertext, PublicKey, SecretKey, Message, Reject]):
    def challenge(self, pk: PublicKey) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext) -> Crypto.Bit: pass

def INDCPA0(pke: Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = pke.KeyGen()
    (m0, m1) = adversary.challenge(pk)
    ct = pke.Encrypt(pk, m0)
    return adversary.guess(ct)

def INDCPA1(pke: Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = pke.KeyGen()
    (m0, m1) = adversary.challenge(pk)
    ct = pke.Encrypt(pk, m1)
    return adversary.guess(ct)


# Notes:
# not sure if ByteStringToMessage and MessageToByteString should be defined in here, or where it is used in KEMfromPKE.  is this a property of the PKE scheme or how it is used?
