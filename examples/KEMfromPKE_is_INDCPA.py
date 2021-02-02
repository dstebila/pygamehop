from typing import Tuple

from gamehop.primitives import Crypto, KEM, PKE
import KEMfromPKE

KEM_Scheme = KEM.Scheme[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext, PKE.Message, Crypto.Reject]
INDCPA_adversary = KEM.INDCPA_adversary[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext, PKE.Message, Crypto.Reject]


# G0 should equal KEM.INDCPA_real with KEMfromPKE inlined
# but we need to include the pke as a parameter
# and specify all the type parameters
def G0(adversary: INDCPA_adversary, pke: PKE.Scheme) -> Crypto.Bit:
    #First need to inline the scheme constructor
    # inlined from KEMfromPKE.py __init__()
    kem_self_pke = pke

    # inlined from KEMfromPKE.py
    (pk, sk) = kem_self_pke.KeyGen()

    # inlined from KEMfromPKE.py
    kem_lv_ss = Crypto.UniformlySample(kem_self_pke.MessageSet)
    kem_lv_ct = kem_self_pke.Encrypt(pk, kem_lv_ss)
    (ct, ss_real) = (kem_lv_ct, kem_lv_ss)

    return adversary.guess(pk, ct, ss_real)

import sys
sys.path.append("..") # Adds higher directory to python modules path.
import gamehop.verification

import ast
s1 = gamehop.verification.canonicalize_function(G0)
print(s1)
# print(ast.dump(ast.parse(gamehop.verification.canonicalize_function(G0)), indent=2))
test1 = gamehop.verification.inline_argument(KEM.INDCPA_real, 'kem', KEMfromPKE.Scheme)
#print(test1)
s2 = gamehop.verification.canonicalize_function(test1)
print(s2)
print("---------------Diff-----------------")
gamehop.verification.stringDiff(s1, s2)
print("------------------------------------")

# G1 should be KEM.INDCPA_random with KEMfromPKE inlined
def G1(adversary: INDCPA_adversary, pke: PKE.Scheme) -> Crypto.Bit:
    #First need to inline the scheme constructor
    # inlined from KEMfromPKE.py __init__()
    kem_self_pke = pke

    # inlined from KEMfromPKE.py
    (pk, sk) = kem_self_pke.KeyGen()

    # inlined from KEMfromPKE.py
    kem_lv_ss = Crypto.UniformlySample(kem_self_pke.MessageSet)
    kem_lv_ct = kem_self_pke.Encrypt(pk, kem_lv_ss)
    (ct, _) = (kem_lv_ct, kem_lv_ss)

    ss_rand =  Crypto.UniformlySample(kem_self_pke.MessageSet)
    return adversary.guess(pk, ct, ss_rand)


s1 = gamehop.verification.canonicalize_function(G1)
print(s1)
# print(ast.dump(ast.parse(gamehop.verification.canonicalize_function(G0)), indent=2))
test1 = gamehop.verification.inline_argument(KEM.INDCPA_random, 'kem', KEMfromPKE.Scheme)
#print(test1)
s2 = gamehop.verification.canonicalize_function(test1)
print(s2)
print("---------------Diff-----------------")
gamehop.verification.stringDiff(s1, s2)
print("------------------------------------")

# Game hop from G0 to G1
# Proven by constructing reduction from distinguishing G0 and G1 to distinguishing PKE.INDCPA0 from PKE.INDCPA1
class R01(PKE.INDCPA_adversary):
    def __init__(self, pke: PKE.Scheme, kem_adversary: INDCPA_adversary):
        self.kem_adversary = kem_adversary
        self.pke = pke

    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk = pk

        self.ss0 = Crypto.UniformlySample(self.pke.MessageSet)
        self.ct0 = self.pke.Encrypt(pk, self.ss0)
        self.m0 = self.ss0

        self.ss1 = Crypto.UniformlySample(self.pke.MessageSet)
        self.ct1 = self.pke.Encrypt(pk, self.ss1)
        self.m1 = self.ss1

        return (self.m0, self.m1)

    def guess(self, ct: PKE.Ciphertext) -> Crypto.Bit:
        return self.kem_adversary.guess(self.pk, ct, self.m0)



# When we inline R01 in PKE.INDCPA0, we should get G0
# Let's try doing that manually and see how close we get
def PKE_INDCPA0_R01(pke: PKE.Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    # First need to inline scheme constructor
    r01_self_kem_adversary = adversary
    r01_self_pke = pke

    (pk, sk) = pke.KeyGen()

    #inlined from R01.challenge()
    r01_self_pk = pk

    r01_self_ss0 = Crypto.UniformlySample(r01_self_pke.MessageSet)
    r01_self_ct0 = r01_self_pke.Encrypt(pk, r01_self_ss0)
    r01_self_m0 = r01_self_ss0

    r01_self_ss1 = Crypto.UniformlySample(r01_self_pke.MessageSet)
    r01_self_ct1 = r01_self_pke.Encrypt(pk, r01_self_ss1)
    r01_self_m1 = r01_self_ss1

    (m0, m1) =  (r01_self_m0, r01_self_m1)

    ct = pke.Encrypt(pk, m0)

    #inlined from R01.guess()
    return r01_self_kem_adversary.guess(r01_self_pk, ct, r01_self_m0)




# When we inline R01 in PKE.INDCPA1, we should get G1
# Let's try doing that manually and see how close we get
def PKE_INDCPA1_R01(pke: PKE.Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    # First need to inline scheme constructor
    r01_self_kem_adversary = adversary
    r01_self_pke = pke

    (pk, sk) = pke.KeyGen()

    #inlined from R01.challenge()
    r01_self_pk = pk

    r01_self_ss0 = Crypto.UniformlySample(r01_self_pke.MessageSet)
    r01_self_ct0 = r01_self_pke.Encrypt(pk, r01_self_ss0)
    r01_self_m0 = r01_self_ss0

    r01_self_ss1 = Crypto.UniformlySample(r01_self_pke.MessageSet)
    r01_self_ct1 = r01_self_pke.Encrypt(pk, r01_self_ss1)
    r01_self_m1 = r01_self_ss1

    (m0, m1) =  (r01_self_m0, r01_self_m1)

    ct = pke.Encrypt(pk, m1)

    #inlined from R01.guess()
    return r01_self_kem_adversary.guess(r01_self_pk, ct, r01_self_m0)
