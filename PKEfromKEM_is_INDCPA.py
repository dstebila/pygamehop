from typing import cast, Any, Callable, Tuple

import Crypto
import KDF
import KEM
import OTP
import PKE
import PKEfromKEM

# G0 should equal PKE.INDCPA0 with PKEfromKEM inlined
def G0(kem: KEM.Scheme, kdf: KDF.Scheme, adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    # manually inline (pk, sk) = pke.KeyGen()
    (v0, v1) = kem.KeyGen()
    (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
    (m0, m1) = adversary.challenge(pk)
    # manually inline ct = pke.Encrypt(pk, m0)
    (v2, v3) = kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
    v4 = kdf.F(v3, "")
    v5 = v4 ^ cast(Crypto.ByteString, m0)
    ct = PKEfromKEM.Ciphertext(v2, v5)
    return adversary.guess(ct)

# Game hop from G0 to G1
# Proven by constructing reduction from distinguishing G0 and G1 to distinguishing KEM.INDCPA_real and KEM.INDCPA_random
class R01(KEM.INDCPA_adversary):
    
    def __init__(self, kdf: KDF.Scheme, pke_adversary: PKE.INDCPA_adversary):
        self.kdf = kdf
        self.pke_adversary = pke_adversary

    def guess(self, pk: KEM.PublicKey, ct_in: KEM.Ciphertext, ss_in: KEM.SharedSecret) -> Crypto.Bit:
        (pkepk, pkesk)  = (PKEfromKEM.PublicKey(pk), PKEfromKEM.SecretKey(sk))
        (m0, m1) = self.pke_adversary.challenge(pkepk)
        (v2, v3) = (ct_in, ss_in)
        v4 = self.kdf.F(v3, "")
        v5 = v4 ^ cast(Crypto.ByteString, m0)
        ct = PKEfromKEM.Ciphertext(v2, v5)
        return self.pke_adversary.guess(ct)

# When we inline R01 in KEM.INDCPA_real, we should get G0
# Let's try doing that manually and see how close we get
def KEM_INDCPAreal_R01(kem: KEM.Scheme, kdf: KDF.Scheme, pke_adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = kem.KeyGen()
    (ct, ss_real) = kem.Encaps(pk)
    # manually inline return adversary.guess(pk, ct, ss_real)
    (pkepk, pkesk)  = (PKEfromKEM.PublicKey(pk), PKEfromKEM.SecretKey(sk))
    (m0, m1) = pke_adversary.challenge(pkepk)
    v4 = kdf.F(ss_real, "")
    v5 = v4 ^ cast(Crypto.ByteString, m0)
    ct_pke = PKEfromKEM.Ciphertext(ct, v5)
    return pke_adversary.guess(ct_pke)

# When we inline R01 in KEM.INDCPA_random, we should get G1
# Let's try doing that manually and see how close we get
def KEM_INDCPArandom_R01(kem: KEM.Scheme, kdf: KDF.Scheme, pke_adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = kem.KeyGen()
    (ct, _) = kem.Encaps(pk)
    ss_rand = KEM.RandomSharedSecret()
    # manually inline return adversary.guess(pk, ct, ss_rand)
    (m0, m1) = pke_adversary.challenge(PKEfromKEM.PublicKey(pk))
    v4 = kdf.F(ss_rand, "")
    v5 = v4 ^ cast(Crypto.ByteString, m0)
    ct_pke = PKEfromKEM.Ciphertext(ct, v5)
    return pke_adversary.guess(ct_pke)

# G1 replaces KEM shared secret with random
def G1(kem: KEM.Scheme, kdf: KDF.Scheme, adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    (v0, v1) = kem.KeyGen()
    (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
    (m0, m1) = adversary.challenge(pk)
    (v2, _) = kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
    v3 = KEM.RandomSharedSecret()
    v4 = kdf.F(v3, "")
    v5 = v4 ^ cast(Crypto.ByteString, m0)
    ct = PKEfromKEM.Ciphertext(v2, v5)
    return adversary.guess(ct)

# Game hop from G1 to G2
# Proven by constructing reduction from distinguishing G1 and G2 to distinguishing KDF.KDF_real from KDF.KDF_random
class R12(KDF.KDF_adversary):
    
    def __init__(self, kem: KEM.Scheme, pke_adversary: PKE.INDCPA_adversary):
        self.kem = kem
        self.pke_adversary = pke_adversary

    def guess(self, oracle: Callable[[Any, Any], Crypto.ByteString]) -> Crypto.Bit:
        (v0, v1) = self.kem.KeyGen()
        (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
        (m0, m1) = self.pke_adversary.challenge(pk)
        (v2, _) = self.kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
        v3 = KEM.RandomSharedSecret()
        v4 = oracle(v3, "")
        v5 = v4 ^ cast(Crypto.ByteString, m0)
        ct = PKEfromKEM.Ciphertext(v2, v5)
        return self.pke_adversary.guess(ct)

# When we inline R12 in KDF.KDF_real, we should get G1
# Let's try doing that manually and see how close we get
def KDF_KDFreal_R12(kem: KEM.Scheme, kdf: KDF.Scheme, pke_adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    # directly substitute oracle = lambda k, x: kdf.F(k, x)
    # manually inline return adversary.guess(oracle)
    (v0, v1) = kem.KeyGen()
    (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
    (m0, m1) = pke_adversary.challenge(pk)
    (v2, _) = kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
    v3 = KEM.RandomSharedSecret()
    v4 = kdf.F(v3, "")
    v5 = v4 ^ cast(Crypto.ByteString, m0)
    ct = PKEfromKEM.Ciphertext(v2, v5)
    return pke_adversary.guess(ct)

# When we inline R12 in KDF.KDF_random, we should get G2
# Let's try doing that manually and see how close we get
def KDF_KDFrandom_R12(kem: KEM.Scheme, kdf: KDF.Ideal, pke_adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    # directly substitute oracle = lambda k, x: kdf.F(k, x)
    # manually inline return adversary.guess(oracle)
    (v0, v1) = kem.KeyGen()
    (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
    (m0, m1) = pke_adversary.challenge(pk)
    (v2, _) = kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
    v3 = KEM.RandomSharedSecret()
    v4 = kdf.F(v3, "")
    v5 = v4 ^ cast(Crypto.ByteString, m0)
    ct = PKEfromKEM.Ciphertext(v2, v5)
    return pke_adversary.guess(ct)

# G2 replaces KDF with ideal function
def G2(kem: KEM.Scheme, kdf: KDF.Ideal, adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    (v0, v1) = kem.KeyGen()
    (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
    (m0, m1) = adversary.challenge(pk)
    (v2, _) = kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
    v3 = KEM.RandomSharedSecret()
    v4 = kdf.F(v3, "")
    v5 = v4 ^ cast(Crypto.ByteString, m0)
    ct = PKEfromKEM.Ciphertext(v2, v5)
    return adversary.guess(ct)

# Game hop from G2 to G3
# Proven by constructing reduction from distinguishing G2 and G3 to distinguishing OTP.OTPCPA0 and OTP.OTPCPA1
class R23(OTP.OTP_adversary):
    
    def __init__(self, kem: KEM.Scheme, kdf: KDF.Ideal, pke_adversary: PKE.INDCPA_adversary):
        self.kem = kem
        self.pke_adversary = pke_adversary
        self.kdf = kdf
        (self.v0, self.v1) = self.kem.KeyGen()
        (self.pk, self.sk) = (PKEfromKEM.PublicKey(self.v0), PKEfromKEM.SecretKey(self.v1))
        (self.m0, self.m1) = self.pke_adversary.challenge(self.pk)
        (self.v2, _) = self.kem.Encaps(cast(PKEfromKEM.PublicKey, self.pk).pk)
        self.v3 = KEM.RandomSharedSecret()
        self.v4 = self.kdf.F(self.v3, "")

    def setkey(self) -> Crypto.UniformlyRandomByteString:
        return self.v4

    def challenge(self) -> Tuple[Crypto.ByteString, Crypto.ByteString]:
        return (cast(Crypto.ByteString, self.m0), cast(Crypto.ByteString, self.m1))

    def guess(self, ct_in: Crypto.ByteString) -> Crypto.Bit:
        ct = PKEfromKEM.Ciphertext(self.v2, ct_in)
        return self.pke_adversary.guess(ct)

# When we inline R23 in OTP.OTPCPA0, we should get G2
# Let's try doing that manually and see how close we get
def OTP_OTPCPA0_R23(kem: KEM.Scheme, kdf: KDF.Ideal, pke_adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    # manually inline R23.__init__
    (v0, v1) = kem.KeyGen()
    (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
    (z0, z1) = pke_adversary.challenge(pk)
    (v2, _) = kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
    v3 = KEM.RandomSharedSecret()
    v4 = kdf.F(v3, "")
    # manually inline mask = adversary.setkey()
    mask = v4
    # manually inline (m0, m1) = adversary.challenge()
    (m0, m1) = (cast(Crypto.ByteString, z0), cast(Crypto.ByteString, z1))
    # manually inline ct = otp.Enc(mask, m0)
    ct = mask ^ m0
    # manually inline return adversary.guess(ct)
    w0 = PKEfromKEM.Ciphertext(v2, ct)
    return pke_adversary.guess(w0)

# When we inline R23 in OTP.OTPCPA1, we should get G3
# Let's try doing that manually and see how close we get
def OTP_OTPCPA1_R23(kem: KEM.Scheme, kdf: KDF.Ideal, pke_adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    # manually inline R23.__init__
    (v0, v1) = kem.KeyGen()
    (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
    (z0, z1) = pke_adversary.challenge(pk)
    (v2, _) = kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
    v3 = KEM.RandomSharedSecret()
    v4 = kdf.F(v3, "")
    # manually inline mask = adversary.setkey()
    mask = v4
    # manually inline (m0, m1) = adversary.challenge()
    (m0, m1) = (cast(Crypto.ByteString, z0), cast(Crypto.ByteString, z1))
    # manually inline ct = otp.Enc(mask, m1)
    ct = mask ^ m1
    # manually inline return adversary.guess(ct)
    w0 = PKEfromKEM.Ciphertext(v2, ct)
    return pke_adversary.guess(w0)

# G3 encrypts m1 not m0
def G3(kem: KEM.Scheme, kdf: KDF.Ideal, adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    (v0, v1) = kem.KeyGen()
    (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
    (m0, m1) = adversary.challenge(pk)
    (v2, _) = kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
    v3 = KEM.RandomSharedSecret()
    v4 = kdf.F(v3, "")
    v5 = v4 ^ cast(Crypto.ByteString, m1)
    ct = PKEfromKEM.Ciphertext(v2, v5)
    return adversary.guess(ct)

# Game hop from G3 to G4
# Proven by constructing reduction from distinguishing G3 and G4 to distinguishing KDF.KDF_random from KDF.KDF_real
# Similar to hop from G1 to G2 (but reversed); omitted for now

# G4 replaces ideal KDF with real function
def G4(kem: KEM.Scheme, kdf: KDF.Scheme, adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    (v0, v1) = kem.KeyGen()
    (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
    (m0, m1) = adversary.challenge(pk)
    (v2, _) = kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
    v3 = KEM.RandomSharedSecret()
    v4 = kdf.F(v3, "")
    v5 = v4 ^ cast(Crypto.ByteString, m1)
    ct = PKEfromKEM.Ciphertext(v2, v5)
    return adversary.guess(ct)

# Game hop from G4 to G5
# Proven by constructing reduction from distinguishing G4 and G5 to distinguishing KEM.INDCPA_random and KEM.INDCPA_real
# Similar to hop from G0 to G1 (but reversed); omitted for now

# G5 replaces random KEM shared secret with real
# G5 should equal PKE.INDCPA1 with PKEfromKEM inlined
def G5(kem: KEM.Scheme, kdf: KDF.Scheme, adversary: PKE.INDCPA_adversary) -> Crypto.Bit:
    (v0, v1) = kem.KeyGen()
    (pk, sk) = (PKEfromKEM.PublicKey(v0), PKEfromKEM.SecretKey(v1))
    (m0, m1) = adversary.challenge(pk)
    (v2, v3) = kem.Encaps(cast(PKEfromKEM.PublicKey, pk).pk)
    v4 = kdf.F(v3, "")
    v5 = v4 ^ cast(Crypto.ByteString, m1)
    ct = PKEfromKEM.Ciphertext(v2, v5)
    return adversary.guess(ct)

