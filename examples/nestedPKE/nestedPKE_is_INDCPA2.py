import gamehop.inlining
from gamehop.primitives import PKE

from nestedPKE import NestedPKE

s = gamehop.inlining.inline_scheme_into_game(NestedPKE, PKE.INDCPA_Left)
print(s)
