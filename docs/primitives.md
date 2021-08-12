# Cryptographic primitives and security experiments

pygamehop has a variety of generic cryptographic primitives and corresponding security experiments defined.  These are contained in the `gamehop/primitives` directory.

## Primitives

Cryptographic primitives are defined as classes that extend the `gamehop.Crypto.Scheme` class. A primitive will typically be accompanied by classes defining associated spaces, such as key spaces or message spaces.

## Experiments

Security experiments are classes that extend a subclass of the `gamehop.proofs.Experiment` class.  So far, there is one such subclass:

- `gamehop.proofs.DistinguishingExperiment`: A distinguishing experiment has two member functions: `main0` and `main1`, both of which take as input a scheme and adversary, and output a bit. This represents a security experiment where the adversary is interacting with one of two worlds and we measure the probability the adversary's output in the two experiments differs.

Each experiment is associated to an adversary class (extending `gamehop.Crypto.Adversary`) which defines the interfaces the adversary exposes to the experiment. For example, for public key encryption this might consist of a first "challenge" phase and a second "guess" phase (see `gamehop.primitives.PKE.PKEINDCPA_adversary`).

## Common utilities

Defined in: `gamehop/primitives/Crypto.py`

This helper class includes:

- `Crypto.Bit`: An abstract data type representing a single bit.
- `Crypto.ByteString`: An abstract data type for representing byte strings.
- `Crypto.UniformlySample(s)`: A function representing arbitrarily sampling from a set `s`.
- `Crypto.Reject`: A rejection/failure symbol.

## List of built-in primitives and experiments

- [Key derivation functions (KDFs)](#key-derivation-functions-kdfs)
- [Key encapsulation mechanisms (KEMs)](#key-encapsulation-mechanisms-kems)
- [One-time pad encryption (OTP)](#one-time-pad-encryption-otp)
- [Public key encryption (PKE)](#public-key-encryption-pke)

### Key derivation functions (KDFs)

Defined in: `gamehop/primitives/KDF.py`

**Primitive.** `KDFScheme.KDF` takes as input a key, a label (represented as a string), and a length (represented as an integer), and outputs a byte string (represented as a Crypto.ByteString).

**Associated spaces:** `Key`.

**Security experiment.** `KDFScheme.KDFsec` is a distinguishing experiment representing indistinguishability of KDF output from random.  The adversary is given access to an oracle that outputs real KDF outputs (in `main0`) or random byte strings `main1`).

### Key encapsulation mechanisms (KEMs)

Defined in: `gamehop/primitives/KEM.py`

**Primitive.** A `KEMScheme` consists of three algorithms:

- `KEMScheme.KeyGen` outputs a public key and a secret key.
- `KEMScheme.Encaps` takes as input a public key and outputs a ciphertext and a shared secret.
- `KEMScheme.Decaps` takes as input a secret key and a ciphertext, and outputs a shared secret (or rejection symbol).

**Associated spaces:** `PublicKey`, `SecretKey`, `Ciphertext`, `SharedSecret`.

**Security experiment.** `KEMScheme.INDCPA` is a distinguishing experiment representing indistinguishability of KEM shared secrets from random under a chosen plaintext attack.  The adversary is given a KEM public key and ciphertext and either the real shared secret for that ciphertext (`main0`) or a randomly chosen value (`main1`).

### One-time pad encryption (OTP)

Defined in: `gamehop/primitives/OTP.py`

**Primitive.** An `OTPScheme` models XORing (`^`) a message with a key.

**Associated spaces:** `Message`.

**Security experiment.** `OTPScheme.OTIND` is a distinguishing experiment representing semantic security of one-time pad encryption.  The adversary can pick two messages and is given a ciphertext that is the one-time pad encryption of either the first message (`main0`) or the second message (`main1`) under a random key.

### Public key encryption (PKE)

Defined in: `gamehop/primitives/PKE.py`

**Primitive.** An `PKEScheme` consists of three algorithms:

- `PKEScheme.KeyGen` outputs a public key and a secret key.
- `PKEScheme.Encrypt` takes as input a public key and a message, and outputs a ciphertext.
- `PKEScheme.Decrypt` takes as input a secret key and a ciphertext, and outputs a message (or rejection symbol).

**Associated spaces:** `PublicKey`, `SecretKey`, `Ciphertext`, `Message`.

**Security experiment.** `PKEScheme.INDCPA` is a distinguishing experiment representing semantic security of public key encryption under a chosen plaintext attack.  The adversary is given a PKE public key, then can pick two messages, and is given a ciphertext that is an encryption of either the first message (`main0`) or the second message (`main1`).
