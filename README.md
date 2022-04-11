# pygamehop

pygamehop is a work-in-progress tool aimed to support cryptographers writing game hopping proofs.  The main goal of pygamehop is to allow a cryptographer to specify a cryptographic scheme and security property in a pseudocode-like subset of Python, encode the steps of a game-hopping proof (including reductions), and have the tool partially or fully check the sequence of games.

Created by Matthew McKague (Queensland University of Technology) and Douglas Stebila (University of Waterloo).

## Current status

This repository is very much a work-in-progress, and is not intended for general use, but may be of interest to people wondering about the project.

## Getting started

pygamehop requires Python 3.9 or higher.  Clone the repository, install the requirements, and set an environment variable for the working directory:

	git clone git@github.com:dstebila/pygamehop
	cd pygamehop
    python3 --version
    # should be 3.9 or higher
    pip3 install -r requirements.txt
    PYTHONPATH=`pwd`; export PYTHONPATH

Now you can run an example. There are 5 working examples at the moment:

- **examples/KEMfromPKE**: A key encapsulation mechanism (KEM) built from a public key encryption scheme; including a proof that, if the PKE is IND-CPA-secure, then the KEM is IND-CPA-secure.
- **examples/PKEfromKEM**: A public key encryption scheme built from a KEM; including a proof that, if the KEM is IND-CPA-secure, then the PKE is IND-CPA-secure.
- **examples/parallelPKE**: A public key encryption scheme built by running two PKEs in parallel; including a proof that the parallel PKE is IND-CPA-secure if both contributing PKEs are IND-CPA-secure.
- **examples/nestedPKE**: A public key encryption scheme built by running two PKEs one after the other; including two proofs that the nested PKE is IND-CPA-secure if either contributing PKE is IND-CPA-secure.
- **examples/SymEnc_CPADollar**: A proof that a symmetric encryption scheme that is indistinguishable from random under chosen plaintext attacks (IND$-CPA) is IND-CPA-secure.

A good starting example is examples/KEMfromPKE/KEMfromPKE_is_INDCPA.py.

- First, take a look (in an editor) at `gamehop/primitives/KEM.py` and `gamehop/primitives/PKE.py`, which show the API definition and IND-CPA security properties for KEMs and PKEs.
- Next, look (in an editor) at `examples/KEMfromPKE/KEMfromPKE.py`, which is a generic construction of a KEM from a PKE scheme.
- Finally, we move on to the proof in `examples/KEMfromPKE/KEMfromPKE_is_INDCPA.py`.  
	- Open up the file in an editor and you'll see a 3-step game hopping proof.  
		- The central hop of the proof involves a reduction to the IND-CPA security property of the PKE; the reduction is explicitly given in the file.  
		- There are also two rewriting hops that encode a fact about length that is not known to the proof engine, and must be checked manually.  
	- You can run the proof by typing `python3 examples/KEMfromPKE/KEMfromPKE_is_INDCPA.py`.  How much detail is printed can be configured in the `proof.check` line inside the file, but the default at the moment prints out every game hop, along with the canonicalization of every game, and the diffs between the games. 
	- A visualization of the game hops is auto-generated and can be found in `docs/images/KEMfromPKE_is_INDCPA.png`, also shown below:

<img src="docs/images/KEMfromPKE_is_INDCPA.png">

## Documentation

You can see more explanation of the examples in `docs/examples.md`. Also in the `docs` folder are notes about the primitives available so far, and the inlining and canonicalization procedures.  Unfortunately this documentation is somewhat out-of-date at the moment; the main ideas are still there, but some of the details have changed.

## Limitations

This is highly incomplete work and has many flaws.  At this point it's trying to be a proof of concept.  

## Contact us

If you're interested in this project, email us at matthew.mckague@qut.edu.au and dstebila@uwaterloo.ca to discuss next steps.  There's a lot of work to be done before this is ready for widespread use, but we'd love some help!
