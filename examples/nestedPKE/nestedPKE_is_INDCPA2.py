from typing import cast, Tuple, Type

import gamehop.inlining
import gamehop.verification
from gamehop.primitives import Crypto, PKE
from gamehop.proofs2 import Proof
import gamehop.utils

from nestedPKE import NestedPKE, PKE1, PKE2

# Theorem: NestedPKE[PKE1, PKE2] is IND-CPA-secure if either PKE1 is IND-CPA-secure or PKE2 is IND-CPA-secure.
# This shown via two separate proofs:
# 1) If PKE1 is IND-CPA-secure, then NestedPKE[PKE1, PKE2] is IND-CPA-secure.
# 2) If PKE2 is IND-CPA-secure, then NestedPKE[PKE1, PKE2] is IND-CPA-secure.

# First proof: If PKE1 is IND-CPA-secure, then NestedPKE[PKE1, PKE2] is IND-CPA-secure.
# This is the statement we're trying to prove: NestedPKE is IND-CPA-secure.
proof1 = Proof(NestedPKE, PKE.INDCPA)

# Game 0 is the NestedPKE scheme inlined into PKE.INDCPA_Left (where m0 is encrypted).

# Game 1 encrypts m1 rather than m0.
# Game 1 is equivalent to the NestedPKE scheme inlined into PKE.INDCPA_Right (where m1 is encrypted).

# Game 0 and Game 1 are indistinguishable under the assumption that PKE1 is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against PKE1,
# and checking that this reduction, inlined into the IND-CPA experiment for PKE1, 
# is equivalent to either Game 0 or Game 1.
class R1(PKE.INDCPA_Adversary, Crypto.Reduction): # This is an INDCPA adversary for PKE1
    def __init__(self, Scheme: Type[PKE1], inner_adversary: PKE.INDCPA_Adversary):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the NestedPKE adversary
    def challenge(self, pk1: PKE1.PublicKey) -> Tuple[PKE1.Message, PKE1.Message]:
        # Use the NestedPKE adversary to generate the two challenge messages.
        # To construct the NestedPKE public key, we use the PKE1 public key given 
        # by the INDCPA challenger for PKE1, and generate the PKE2 keypair ourselves.
        (self.pk2, self.sk2) = PKE2.KeyGen()
        pk_double = NestedPKE.PublicKey(pk1, self.pk2)
        (m0, m1) = self.inner_adversary.challenge(pk_double)
        return (m0, m1)
    def guess(self, ct1: PKE1.Ciphertext) -> Crypto.Bit:
        # Given the challenge PKE1 ciphertext from the INDCPA challenger for PKE1,
        # construct a NestedPKE ciphertext by encrypting it under the PKE2 public key,
        # then pass the NestedPKE ciphertext to the NestedPKE adversary.
        pt2 = cast(PKE2.Message, ct1) # Treat the PKE1 ciphertext as a PKE2 message
        ct2 = PKE2.Encrypt(self.pk2, pt2)
        ctprime = cast(NestedPKE.Ciphertext, ct2) # Treat the PKE2 ciphertext as a NestedPKE ciphertext
        return self.inner_adversary.guess(ctprime)

proof1.add_distinguishing_proof_step(R1, PKE.INDCPA, PKE1)

assert proof1.check(print_hops=False, print_canonicalizations=False)
print(proof1.advantage_bound())
