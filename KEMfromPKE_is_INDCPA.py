from typing import cast, Tuple

import Crypto
import KEM
import PKE
import KEMfromPKE

# G0 should equal KEM.INDCPA_real with KEMfromPKE inlined
def G0(pke: PKE.Scheme, adversary: KEM.INDCPA_adversary) -> Crypto.Bit:

    # manually inline (pk, sk) = kem.KeyGen()
    (v0, v1) = pke.KeyGen()
    (pk, sk) = (KEMfromPKE.PublicKey(v0), KEMfromPKE.SecretKey(v1))

    # manually inline (ct, ss_real) = kem.Encaps(pk)
    v2 = Crypto.UniformlyRandomByteString()
    v3 = pke.Encrypt(cast(KEMfromPKE.PublicKey, pk).pk, cast(PKE.Message, v2))
    (ct, ss_real) = (KEMfromPKE.Ciphertext(v3), KEMfromPKE.SharedSecret(v2))

    return adversary.guess(pk, ct, ss_real)

# G1 should be KEM.INDCPA_random with KEMfromPKE inlined
def G1(pke: PKE.Scheme, adversary: KEM.INDCPA_adversary) -> Crypto.Bit:

    # manually inline (pk, sk) = kem.KeyGen()
    (v0, v1) = pke.KeyGen()
    (pk, sk) = (KEMfromPKE.PublicKey(v0), KEMfromPKE.SecretKey(v1))

    # manually inline (ct, _) = kem.Encaps(pk)
    v2 = Crypto.UniformlyRandomByteString()
    v3 = pke.Encrypt(cast(KEMfromPKE.PublicKey, pk).pk, cast(PKE.Message, v2))
    (ct, _) = (KEMfromPKE.Ciphertext(v3), KEMfromPKE.SharedSecret(v2))

    ss_rand = KEM.RandomSharedSecret()
    return adversary.guess(pk, ct, ss_rand)

# Game hop from G0 to G1
# Proven by constructing reduction from distinguishing G0 and G1 to distinguishing PKE.INDCPA0 from PKE.INDCPA1
class R01(PKE.INDCPA_adversary):
    
    def __init__(self, kem_adversary: KEM.INDCPA_adversary):
        self.kem_adversary = kem_adversary

    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk = pk
        self.m0 = Crypto.UniformlyRandomByteString()
        self.m1 = KEM.RandomSharedSecret()
        return (cast(PKE.Message, self.m0), cast(PKE.Message, self.m1))

    def guess(self, ct: PKE.Ciphertext) -> Crypto.Bit:
        return self.kem_adversary.guess(KEMfromPKE.PublicKey(self.pk), KEMfromPKE.Ciphertext(ct), KEMfromPKE.SharedSecret(self.m0))

# When we inline R01 in PKE.INDCPA0, we should get G0
# Let's try doing that manually and see how close we get
def PKE_INDCPA0_R01(pke: PKE.Scheme, kem_adversary: KEM.INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = pke.KeyGen()
    # manually inline (m0, m1) = adversary.challenge(pk)
    z0 = Crypto.UniformlyRandomByteString()
    z1 = KEM.RandomSharedSecret()
    (m0, m1) = (cast(PKE.Message, z0), cast(PKE.Message, z1))
    ct = pke.Encrypt(pk, m0)
    # manually inline return adversary.guess(ct)
    return kem_adversary.guess(KEMfromPKE.PublicKey(pk), KEMfromPKE.Ciphertext(ct), KEMfromPKE.SharedSecret(z0))

# When we inline R01 in PKE.INDCPA1, we should get G1
# Let's try doing that manually and see how close we get
def PKE_INDCPA1_R01(pke: PKE.Scheme, kem_adversary: KEM.INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = pke.KeyGen()
    # manually inline (m0, m1) = adversary.challenge(pk)
    z0 = Crypto.UniformlyRandomByteString()
    z1 = KEM.RandomSharedSecret()
    (m0, m1) = (cast(PKE.Message, z0), cast(PKE.Message, z1))
    ct = pke.Encrypt(pk, m1)
    # manually inline return adversary.guess(ct)
    return kem_adversary.guess(KEMfromPKE.PublicKey(pk), KEMfromPKE.Ciphertext(ct), KEMfromPKE.SharedSecret(z0))

