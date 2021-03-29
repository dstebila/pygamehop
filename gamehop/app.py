import sys
import os
from gamehop import apphelpers as helpers

debugging = True
separator = "---------------------------------------------------------------"
Separator = "==============================================================="

dirname = helpers.parseArgs(sys.argv)
sys.path.append(os.path.abspath(dirname))
import proof

if hasattr(proof, 'debugging'):
    debugging = proof.debugging

if hasattr(proof, 'steps'):
    if not hasattr(proof, 'experiment'):
        print("missing experiment")
        sys.exit(1)

    r, advantages = helpers.checkProof(proof.experiment, proof.steps, debugging)
    print(advantages)
    if r:
        print("Valid")
        sys.exit(0)
    else:
        print("Invalid")
        sys.exit(1)
else:
    if not hasattr(proof, 'proofs'):
        print("Need steps or proofs variable to be defined.")
        sys.exit(1)

    r = True
    for (experiment, steps) in proof.proofs:
        r2, advantages = helpers.checkProof(experiment, steps, debugging)
        print(advantages)
        r = r and r2

    if r:
        print("Valid")
        sys.exit(0)
    else:
        print("Invalid")
        sys.exit(1)
