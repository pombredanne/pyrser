from pyrser import meta
from pyrser.parsing.base import BasicParser


@meta.hook(BasicParser, "dump_nodes")
def dump_nodes(self):
    """
    Dump tag,rule,id and value cache. For debug.

    example::

        R = [
            #dump_nodes
        ]

    """
    print("DUMP NODE")
    try:
        for k, v in self.id_cache.items():
            print("[%d]=%s" % (k, v))
        for k, v in self.rule_nodes.items():
            txt = "['%s']=%d" % (k, id(v))
            if k in self.tag_cache:
                tag = self.tag_cache[k]
                txt += " tag <%s>" % tag
                k = "%d:%d" % (tag._begin, tag._end)
                txt += " cache <%s>" % self._stream.value_cache[k]
            print(txt)
    except Exception as err:
        print("RECV Exception %s" % err)
    import sys
    sys.stdout.flush()
    return True
