# Examples

The `examples` directory contains several examples of constructions and corresponding proofs.

## List of Examples

- [KEMfromPKE](#KEMfromPKE)
- [PKEfromKEM](#PKEfromKEM)

### KEMfromPKE

`examples/KEMfromPKE/KEMfromPKE.py` contains an example in which a key encapsulation mechanism is generically constructed from a public key encryption scheme by having the encapsulator pick a random shared secret and transport it to the decapsulator via public key encryption.

`examples/KEMfromPKE/KEMfromPKE_is_INDCPA.py` contains a proof that this KEM is IND-CPA-secure under the assumption that the public key encryption scheme is IND-CPA-secure. The KEM IND-CPA experiment is a distinguishing experiment defined in `gamehop.primitives.KEM.INDCPA`.  

The proof consists of the following game hops:

- Game 0: `KEMfromPKE` inlined into the "real" version of the KEM IND-CPA game (`KEM.INDCPA.main0`).
- Game 1: `KEMfromPKE` inlined into the "random" version of the KEM IND-CPA game (`KEM.INDCPA.main`).
	- Reduction `R01`: This reduction interpolates between Game 0 and Game 1. It is an IND-CPA adversary against the PKE scheme.

Note that Game 0 and 1 are not explicitly written out in `KEMfromPKE_is_INDCPA.py`, they are derived from the starting and ending points of the proof.

The proof engine checks that:

- Game 0 (`KEMfromPKE` inlined into `KEM.INDCPA.main0`) is equivalent to `R01` inlined into `PKE.INDCPA.main0`.
- `R01` inlined into `PKE.INDCPA.main1` is equivalent to Game 1 (`KEMfromPKE` inlined into `KEM.INDCPA.main1`).

### PKEfromKEM

`examples/PKEfromKEM/PKEfromKEM ` contains an example in which a public key encryption scheme is generically constructed from a key encapsulation mechanism by having taking the shared secret from the encapsulation, applying a key derivation function to construct a mask, and XORing the mask with the message.

`examples/PKEfromKEM/PKEfromKEM_is_INDCPA.py` contains a proof that this PKE is IND-CPA-secure under the assumption that the key encapsulation mechanism is IND-CPA-secure and the key derivation function is a secure KDF. The PKE IND-CPA experiment is a distinguishing experiment defined in `gamehop.primitives.PKE.INDCPA`.  

The proof is a "forwards-and-backwards" proof, in which we start with the "left" version of the PKE IND-CPA game in which the challenge ciphertext encrypts `m0`, replace all the relevant values with random, swap to encrypting `m1`, and then "undo" the replacements switching all random values back to real, yielding the "right" version of the PKE IND-CPA game in which the challenge cipheretxt encrypts `m1`.

The proof consists of the following game hops:

- Game 0: `PKEfromKEM` inlined into the "left" version of the PKE IND-CPA game (`PKE.INDCPA.main0`). Note the challenge ciphertext is the encryption of `m0`.
- Game 1: The KEM shared secret is replaced with a random value.
	- Reduction `R01`: This reduction interpolates between Game 0 and Game 1. It is an IND-CPA adversary against the KEM scheme.
- Game 2: The output of the KDF is replaced with a random value.
	- Reduction `R12`: This reduction interpolates between Game 1 and Game 2. It is an adversary against the security of the KDF scheme.
- Game 3: The challenge ciphertext is switched to be constructed by XORing the random mask with `m1` rather than `m0`.
	- Reduction `R23`: This reduction interpolates between Game 2 and Game 3. It is an adversary against indistinguishability of the one-time pad.  (The reader might wonder why a "reduction" is necessary here, since the one-time pad is information-theoretic rather than computational. In the pygamehop framework, every game transition is connected via a reduction, since the proof engine must be told how to connect two games via the distinguishing of some security property.)
- Game 4: The output of the KDF is replaced with a real value.
	- Reduction `R34`: This reduction interpolates between Game 3 and Game 4. It is an adversary against the security of the KDF scheme.
- Game 5: The KEM shared secret is replaced with a real value.
	- Reduction `R45`: This reduction interpolates between Game 4 and Game 5. It is an IND-CPA adversary against the KEM scheme.
- Game 6: `PKEfromKEM` inlined into the "right" version of the PKE IND-CPA game (`PKE.INDCPA.main1`). Note the challenge ciphertext is the encryption of `m1`.

Note that Game 0 and 6 are not explicitly written out in `PKEfromKEM_is_INDCPA.py`, they are derived from the starting and ending points of the proof. Furthermore, games 1-5 are not explicitly written out, as they are derived from the relevant reductions.

The proof engine checks that:

- Game 0 (`PKEfromKEM` inlined into `PKE.INDCPA.main0`) is equivalent to `R01` inlined into `KEM.INDCPA.main0`.
- `R01` inlined into `KEM.INDCPA.main1` is equivalent to `R12` inlined into `KDF.KDFsec.main0`.
- `R12` inlined into `KDF.KDFsec.main1` is equivalent to `R23` inlined into `OTP.OTIND.main0`.
- `R23` inlined into `OTP.OTIND.main1` is equivalent to `R34` inlined into `KDF.KDFsec.main1`. 
- `R34` inlined into `KDF.KDFsec.main0` is equivalent to `R45` inlined into `KEM.INDCPA.main1`.
- `R45` inlined into `KEM.INDCPA.main0` is equivalent to Game 6 (`PKEfromKEM` inlined into `PKE.INDCPA.main1`).
