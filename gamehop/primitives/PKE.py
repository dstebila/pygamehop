from typing import Tuple, Union, TypeVar, Generic, Set

from . import Crypto

Ciphertext = TypeVar('Ciphertext')
PublicKey = TypeVar('PublicKey')
Reject = Crypto.Reject
SecretKey = TypeVar('SecretKey')
Message = TypeVar('Message')


class PKEScheme(Generic[Ciphertext, PublicKey, SecretKey, Message]):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encrypt(self, pk: PublicKey, msg: Message) -> Ciphertext: pass
    def Decrypt(self, sk: SecretKey, ct: Ciphertext) -> Union[Message, Reject]: pass
    MessageSet: Set[Message] = set()

class PKEINDCPA_adversary(Generic[Ciphertext, PublicKey, SecretKey, Message], Crypto.AdversaryBaseClass):
    def challenge(self, pk: PublicKey) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext) -> Crypto.Bit: pass
    def setup(self, pke: PKEScheme) -> None: pass
    pke: PKEScheme

def INDCPA0(pke: PKEScheme, adversary: PKEINDCPA_adversary) -> Crypto.Bit:
    #adversary.pke = pke
    dummy = adversary.setup(pke)
    (pk, sk) = pke.KeyGen()
    (m0, m1) = adversary.challenge(pk)
    ct = pke.Encrypt(pk, m0)
    r = adversary.guess(ct)
    return r


def INDCPA1(pke: PKEScheme, adversary: PKEINDCPA_adversary) -> Crypto.Bit:
    #adversary.pke = pke
    dummy = adversary.setup(pke)
    (pk, sk) = pke.KeyGen()
    (m0, m1) = adversary.challenge(pk)
    ct = pke.Encrypt(pk, m1)
    r = adversary.guess(ct)
    return r

class PKECORRECT_adversary(Generic[Ciphertext, PublicKey, SecretKey, Message], Crypto.AdversaryBaseClass):
    def challenge(self, pk: PublicKey, sk: SecretKey) -> Tuple[Message, Any]: pass
    def guess(self, m: Message, ct: Ciphertext, pt: Message) -> Crypto.Bit: pass
    def setup(self, pke: PKEScheme) -> None: pass
    pke: PKEScheme

def CORRECT0(pke: PKEScheme, adversary: PKECORRECT_adversary):
    dummy = adversary.setup(pke)
    (pk, sk) = pke.KeyGen()
    m = adversary.challenge(pk, sk)
    ct = pke.Encrypt(pk, m)
    pt = pke.Decrypt(sk, ct)
    r = adversary.guess(m, ct, pt)
    return r
    
def CORRECT1(pke: PKEScheme, adversary: PKECORRECT_adversary):
    dummy = adversary.setup(pke)
    (pk, sk) = pke.KeyGen()
    m = adversary.challenge(pk, sk)
    ct = pke.Encrypt(pk, m)
    pt = pke.Decrypt(sk, ct)
    r = adversary.guess(pt, ct, pt)
    return r


    
CORRECT = (CORRECT0, CORRECT1, PKECORRECT_adversary, 0)

class INDCPA_advantage(Crypto.AdvantageBaseClass): pass
#INDCPA: Crypto.Experiment[ INDCPA_game, INDCPA_advantage ] = (INDCPA0, INDCPA1, PKEINDCPA_adversary, INDCPA_advantage)
INDCPA = (INDCPA0, INDCPA1, PKEINDCPA_adversary, INDCPA_advantage)
