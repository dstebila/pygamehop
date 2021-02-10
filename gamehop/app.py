import sys
import os
from gamehop import apphelpers as helpers

debugging = True
separator = "---------------------------------------------------------------"
Separator = "==============================================================="


dirname = helpers.parseArgs(sys.argv)
sys.path.append(os.path.abspath(dirname))
import proof

if hasattr(proof, 'steps'):
    if not hasattr(proof, 'experiment'):
        print("missing experiment")
        sys.exit(1)

    r = helpers.checkProof(proof.experiment, proof.steps, debugging)
    if r:
        print("Valid")
    else:
        print("Invalid")
    sys.exit(r)
else:
    if not hassattr(proof, 'proofs'):
        print("Need steps or proofs variable to be defined.")
        sys.exit(1)

    r = True
    for p in proof.proofs:
        experiment = p[0]
        steps = p[1]
        r2 = helpers.checkProof(steps, experiment, debugging)
        r = r and r2

    if r:
        print("Valid")
    else:
        print("Invalid")

    sys.exit(r)
