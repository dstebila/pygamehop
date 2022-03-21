from typing import Annotated, Callable, Generic, Sized, Tuple, Type, TypeVar

from . import Crypto
from .. import lists

Key = TypeVar('Key')
Message = TypeVar('Message', bound=Sized)
Tag = TypeVar('Tag')

class MACScheme(Crypto.Scheme, Generic[Key, Message, Tag]):
    @staticmethod
    def uniformKey() -> Annotated[Key, Crypto.UniformlyRandom]: pass
    @staticmethod
    def MAC(k: Key, msg: Message) -> Tag: pass

class EUFCMA_Adversary(Crypto.Adversary, Generic[Key, Message, Tag]):
    def run(self, o_gettag: Callable[[Message], Tag], o_checktag: Callable[[Message, Tag], bool]) -> Crypto.Bit: pass

class EUFCMA_Real(Crypto.Game, Generic[Key, Message, Tag]):
    def __init__(self, Scheme: Type[MACScheme[Key, Message, Tag]], Adversary: Type[EUFCMA_Adversary[Key, Message, Tag]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.k = self.Scheme.uniformKey()
        r = self.adversary.run(self.o_gettag, self.o_checktag)
        return r
    def o_gettag(self, msg: Message) -> Tag:
        tag = self.Scheme.MAC(self.k, msg)
        return tag
    def o_checktag(self, msg: Message, tag: Tag) -> bool:
        tagprime = self.Scheme.MAC(self.k, msg)
        ret = (tag == tagprime)
        return ret

class EUFCMA_Fake(Crypto.Game, Generic[Key, Message, Tag]):
    def __init__(self, Scheme: Type[MACScheme[Key, Message, Tag]], Adversary: Type[EUFCMA_Adversary[Key, Message, Tag]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.k = self.Scheme.uniformKey()
        self.tags = lists.new_empty_list()
        r = self.adversary.run(self.o_gettag, self.o_checktag)
        return r
    def o_gettag(self, msg: Message) -> Tag:
        tag = self.Scheme.MAC(self.k, msg)
        self.tags = lists.append_item(self.tags, (msg, tag))
        return tag
    def o_checktag(self, msg: Message, tag: Tag) -> bool:
        ret = (msg, tag) in self.tags
        return ret

EUFCMA = Crypto.DistinguishingExperimentRealOrRandom("MAC", "EUFCMA", EUFCMA_Real, EUFCMA_Fake, EUFCMA_Adversary)
