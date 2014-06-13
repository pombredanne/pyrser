# around a signature store type resolution for monomorphic or polymorphic call
import inspect
from pyrser import fmt
from pyrser.type_checking.type_name import *
from pyrser.type_checking.signature import *
from pyrser.type_checking.fun import *
from pyrser.type_checking.symbol import *


class EvalCtx:
    """
    Store environment for mono/poly call.
    """

    def __init__(self, sig: Signature):
        self._sig = sig
        self.resolution = dict()
        self.resolve()

    def get_parent(self):
        return self._sig.get_parent()

    def internal_name(self):
        return self._sig.internal_name()

    def show_name(self):
        return self._sig.show_name()

    @property
    def name(self):
        if self._sig is not None:
            return self._sig.name
        return None

    @property
    def tret(self):
        if self._sig is not None and hasattr(self._sig, 'tret'):
            return self._sig.tret
        return None

    @property
    def tparams(self):
        if self._sig is not None and hasattr(self._sig, 'tparams'):
            return self._sig.tparams
        return None

    @property
    def variadic(self):
        if self._sig is not None and hasattr(self._sig, 'variadic'):
            return self._sig.variadic
        return None

    def from_sig(sig: Signature) -> object:
        if isinstance(sig, EvalCtx):
            return sig
        else:
            return EvalCtx(sig)

    def set_parent(self, parent) -> object:
        """
        Forward to intern Signature
        """
        return self._sig.set_parent(parent)

    def __len__(self) -> int:
        return len(self._sig)

    def values(self) -> list:
        """
        Make EvalCtx iterable (to update a scope with it)
        """
        return [self._sig]

    def get_compute_sig(self) -> Signature:
        """
        Compute a signature Using resolution!!!

        TODO: discuss of relevance of a final generation for a signature
        """
        tret = []
        tparams = []
        for t in self.tret.components:
            tret.append(self.resolution[t]().show_name())
        if hasattr(self, 'tparams'):
            for p in self.tparams:
                tp = []
                for t in p.components:
                    tp.append(self.resolution[t]().show_name())
                tparams.append(" ".join(tp))
        ret = Fun(self.name, " ".join(tret), tparams)
        # transform as-is into our internal Signature (Val, Var, whatever)
        ret.__class__ = self._sig.__class__
        return ret

    def set_parent(self, parent) -> object:
        """
        When we add a parent (from Symbol), don't forget to resolve.
        """
        ret = self
        if parent is not None:
            ret = self._sig.set_parent(parent)
            self.resolve()
        elif not hasattr(self, 'parent'):
            # only if parent didn't exist yet
            self.parent = None
        return ret

    def resolve(self):
        """
        Process the signature and find definition for type.
        """
        # collect types for resolution
        t2resolv = []
        if hasattr(self._sig, 'tret'):
            t2resolv.append(self._sig.tret)
        if hasattr(self._sig, 'tparams') and self._sig.tparams is not None:
            for p in self._sig.tparams:
                t2resolv.append(p)
        for t in t2resolv:
            for c in t.components:
                if c not in self.resolution or self.resolution[c] is None:
                    # try to find what is c
                    parent = self.get_parent()
                    if parent is not None:
                        sc = parent.get_by_symbol_name(c)
                        if len(sc) == 1:
                            sc = list(sc.values())[0]
                            # unwrap EvalCtx around Type
                            if isinstance(sc, EvalCtx):
                                sc = sc._sig
                            rtyp = weakref.ref(sc)
                            self.resolution[c] = rtyp
                            continue
                    # unresolved
                    self.resolution[c] = None

    def get_resolved_names(self, type_name: TypeName) -> list:
        """
        Use self.resolution to subsitute type_name.
        Allow to instanciate polymorphic type ?1, ?toto
        """
        if not isinstance(type_name, TypeName):
            raise Exception("Take a TypeName as parameter not a %s"
                            % type(type_name))
        rnames = []
        for name in type_name.components:
            if name not in self.resolution:
                raise Exception("Unknown type %s in a EvalCtx" % name)
            rname = self.resolution[name]
            if rname is not None:
                rname = rname().show_name()
            else:
                rname = name
            rnames.append(rname)
        return rnames

    def set_resolved_name(self, ref: dict, type_name2solve: TypeName,
                          type_name_ref: TypeName):
        """
        Warning!!! Need to rethink it when global poly type
        """
        #print("RESOLVE Use %s" % ref)
        #print("RESOLVE To %s" % self.resolution)
        if self.resolution[type_name2solve.value] is None:
            self.resolution[type_name2solve.value] = ref[type_name_ref.value]

    def to_fmt(self):
        """
        Return an Fmt representation for pretty-printing
        """
        qual = "evalctx"
        lseval = []
        block = fmt.block(":\n", "", fmt.tab(lseval))
        txt = fmt.sep(" ", [qual, block])
        lseval.append(self._sig.to_fmt())
        if len(self.resolution) > 0:
            lsb = []
            for k in sorted(self.resolution.keys()):
                s = self.resolution[k]
                if s is not None:
                    lsb.append(
                        fmt.end(
                            "\n",
                            ["'%s': %s (%s)" % (k, s, s().show_name())]
                        )
                    )
                else:
                    lsb.append(fmt.end("\n", ["'%s': Unresolved" % (k)]))
            lseval.append(fmt.block("\nresolution :\n", "", fmt.tab(lsb)))
        return txt

    def __str__(self):
        return str(self.to_fmt())
