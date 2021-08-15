# Examples

The `examples` directory contains several examples of constructions and corresponding proofs.

## List of Examples

- [KEMfromPKE](#KEMfromPKE)
- [PKEfromKEM](#PKEfromKEM)
- [nestedPKE](#nestedPKE)
- [parallelPKE](#parallelPKE)

### KEMfromPKE

`examples/KEMfromPKE/KEMfromPKE.py` contains an example in which a key encapsulation mechanism is generically constructed from a public key encryption scheme by having the encapsulator pick a random shared secret and transport it to the decapsulator via public key encryption:

1. `ss <- UniformlyRandom(SharedSecret)`
2. `ct <- pke.Encrypt(pk, ss)`

`examples/KEMfromPKE/KEMfromPKE_is_INDCPA.py` contains a proof of the following:

**Theorem.** `KEMfromPKE` is an IND-CPA-secure key encapsulation mechanism under the assumption that `pke` is an IND-CPA-secure public key encryption scheme.

**Proof.** The proof consists of the following game hops:

![KEMfromPKE game hop diagram](images/KEMfromPKE_is_INDCPA.png)

- Starting game: `KEMfromPKE` inlined into the "real" version of the KEM IND-CPA game (`KEM.INDCPA.main0`), where the adversary is challenged with the real shared secret encapsulated in the challenge ciphertext.
- Game 1: A rewrite of the starting game, which uses the fact that two shared secrets selected uniformly at random have the same length.
	- The starting game and game 1 are related via a rewriting step, the validity of which must be manually checked via the diff output by the proof engine.
- Game 2: The shared secret that the adversary is challenged with is changed to be the random value.
	- Game 1 and game 2 are related via an indistinguishability step based on the IND-CPA security of scheme `pke`. Reduction `R12` is an IND-CPA adversary against scheme `pke`. It selects two shared secrets and has its IND-CPA challenger for `pke` encrypt one of them.
- Game 3: A rewrite of game 2, which again uses the fact that two shared secrets selected uniformly at random have the same length.	- Game 2 and game 3 are related via a rewriting step, the validity of which must be manually checked via the diff output by the proof engine.
- Ending game: `KEMfromPKE ` inlined into the "random" version of the KEM IND-CPA game (`KEM.INDCPA.main1`), where the adversary is challenged with a random shared secret rather than the real shared secret encapsulated in the challenge ciphertext.

### PKEfromKEM

`examples/PKEfromKEM/PKEfromKEM ` contains an example in which a public key encryption scheme is generically constructed from a key encapsulation mechanism by having taking the shared secret from the encapsulation, applying a key derivation function to construct a mask, and XORing the mask with the message.

`examples/PKEfromKEM/PKEfromKEM_is_INDCPA.py` contains a proof that this PKE is IND-CPA-secure under the assumption that the key encapsulation mechanism is IND-CPA-secure and the key derivation function is a secure KDF. The PKE IND-CPA experiment is a distinguishing experiment defined in `gamehop.primitives.PKE.INDCPA`.  

The proof is a "forwards-and-backwards" proof, in which we start with the "left" version of the PKE IND-CPA game in which the challenge ciphertext encrypts `m0`, replace all the relevant values with random, swap to encrypting `m1`, and then "undo" the replacements switching all random values back to real, yielding the "right" version of the PKE IND-CPA game in which the challenge cipheretxt encrypts `m1`.

The proof consists of the following game hops:

![PKEfromKEM game hop diagram](images/PKEfromKEM_is_INDCPA.png)

- Starting game: `PKEfromKEM` inlined into the "left" version of the PKE IND-CPA game (`PKE.INDCPA.main0`), in which the challenge ciphertext is the encryption of `m0`.
- Hop 1: A distinguishing step in which the real KEM shared secret is replaced with a random value.
	- Reduction `R01` is an IND-CPA adversary against the KEM scheme that interpolates between the starting game and Game 1.
- Hop 2: A distinguishing step in which the real KDF output is replaced with a random value.
	- Reduction `R12` is an adversary against the security of the KDF scheme that interpolates between Game 1 and Game 2.
- Hop 3: A distinguishing step in which the encryption mask is XORed with `m1` rather than `m0`.
	- Reduction `R23` is an adversary against the one-time indistinguishability security of the one-time pad.  (The reader might wonder why a "reduction" is necessary here, since the one-time pad is information-theoretic rather than computational. In the pygamehop framework, every game transition is connected via a reduction, since the proof engine must be told how to connect two games via the distinguishing of some security property.)
- (We now start "undoing" the replacements as mentioned above.)
- Hop 4: A distinguishing step in which the random value used in place of the KDF output is replaced with the real KDF output.
	- Reduction `R34` is an adversary against the security of the KDF scheme that interpolates between Game 3 and Game 4.
- Hop 5: A distinguishing step in which the random value used in place of the KEM shared secret is replaced with the real KEM shared secret.
	- Reduction `R45` is an IND-CPA adversary against the KEM scheme that interpolates between Game 4 and the ending game.
- Ending game: `PKEfromKEM` inlined into the "right" version of the PKE IND-CPA game (`PKE.INDCPA.main1`), in which the challenge ciphertext is the encryption of `m1`.

Note that the starting and ending games are not explicitly written out in `PKEfromKEM_is_INDCPA.py`, they are derived from the starting and ending points of the proof. Furthermore, intermediate games are not explicitly written out, they are derived from the relevant transformations.

The proof engine checks that:

- The starting game (`PKEfromKEM` inlined into `PKE.INDCPA.main0`) is equivalent to `R01` inlined into `KEM.INDCPA.main0`.
- `R01` inlined into `KEM.INDCPA.main1` is equivalent to `R12` inlined into `KDF.KDFsec.main0`.
- `R12` inlined into `KDF.KDFsec.main1` is equivalent to `R23` inlined into `OTP.OTIND.main0`.
- `R23` inlined into `OTP.OTIND.main1` is equivalent to `R34` inlined into `KDF.KDFsec.main1`. 
- `R34` inlined into `KDF.KDFsec.main0` is equivalent to `R45` inlined into `KEM.INDCPA.main1`.
- `R45` inlined into `KEM.INDCPA.main0` is equivalent to the ending game (`PKEfromKEM` inlined into `PKE.INDCPA.main1`).

### nestedPKE

`examples/nestedPKE/nestedPKE.py` contains an example of a public key encryption scheme which is constructed from two public key encryption schemes `pke1`, `pke2` by **nesting**: `ct = pke2.Encrypt(pk2, pke1.Encrypt(pk1, msg))`.

`examples/nestedPKE.py/nestedPKE.py_is_INDCPA.py` contains proofs that this PKE is IND-CPA-secure under the assumption that either of the two the public key encryption schemes `pke1`, `pke2` is IND-CPA-secure.  Note that this consists of two separate proofs, listed in the same file.

**Theorem.** `nestedPKE` is an IND-CPA-secure public key encryption scheme, under the assumption that `pke1` is IND-CPA-secure.

**Proof.** The proof consists of the following game hops:

![nestedPKE is INDCPA proof 1 game hop diagram](images/nestedPKE_is_INDCPA_proof1.png)

- Starting game: `nestedPKE` inlined into the "left" version of the PKE IND-CPA game (`PKE.INDCPA.main0`), in which the challenge ciphertext is the encryption of `m0`.
- Ending game: `nestedPKE` inlined into the "right" version of the PKE IND-CPA game (`PKE.INDCPA.main1`), in which the challenge ciphertext is the encryption of `m1`.
	- The starting game and ending game are related via an indistinguishability step based on the IND-CPA security of scheme `pke1`. Reduction `R1` is an IND-CPA adversary against scheme `pke1`. It uses the `pke1` IND-CPA challenger to encrypt either `m0` or `m1` and then encrypts the resulting ciphertext using scheme `pke2`.

**Theorem.** `nestedPKE` is an IND-CPA-secure public key encryption scheme, under the assumption that `pke2` is IND-CPA-secure.

**Proof.** The proof consists of the following game hops:

![nestedPKE is INDCPA proof 2 game hop diagram](images/nestedPKE_is_INDCPA_proof2.png)

- Starting game: `nestedPKE` inlined into the "left" version of the PKE IND-CPA game (`PKE.INDCPA.main0`), in which the challenge ciphertext is the encryption of `m0`.
- Game 1: A rewrite of the starting game, which uses the fact that `len(pke1.Encrypt(pk1, m0)) = len(pke1.Encrypt(pk1, m1))` assuming `len(m0) == len(m1)`.
	- The starting game and game 1 are related via a rewriting step, the validity of which must be manually checked via the diff output by the proof engine.
- Game 2: The challenge ciphertext is switched to be the encryption of `m1`.
	- Game 1 and game 2 are related via an indistinguishability step based on the IND-CPA security of scheme `pke2`. Reduction `R2` is an IND-CPA adversary against scheme `pke1`. It encrypts `m0` and `m1` under `pke1` itself, then passes the two resulting ciphertexts to the IND-CPA challenge for `pke2`.
- Game 3: A rewrite of game 2, which again uses the fact that `len(pke1.Encrypt(pk1, m0)) = len(pke1.Encrypt(pk1, m1))` assuming `len(m0) == len(m1)`. 
	- Game 2 and game 3 are related via a rewriting step, the validity of which must be manually checked via the diff output by the proof engine.
- Ending game: `nestedPKE` inlined into the "right" version of the PKE IND-CPA game (`PKE.INDCPA.main1`), in which the challenge ciphertext is the encryption of `m1`.
