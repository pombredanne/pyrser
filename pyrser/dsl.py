from pyrser import parsing
from pyrser import meta


class EBNF(parsing.Parser):
    """Basic class for BNF DSL PARSING."""
    def get_rules(self) -> parsing.Node:
        res = self.eval_rule('bnf_dsl')
        if not res:
            raise meta.ParseError("Parse error with the rule {rule!r}",
                                  stream_name=self._stream.name,
                                  rule='bnf_dsl',
                                  pos=self._stream._cursor.max_readed_position,
                                  line=self._stream.last_readed_line)
        return res

    def __init__(self, stream=''):
        super().__init__(stream)
        #TODO(iopi): allow comment, so ignoreCxx
        self.set_rules({
            #
            # bnf_dsl ::= [rule : r #add_rules(_, r) ]+ Base.eof
            # ;
            #
            'bnf_dsl': parsing.Seq(
                parsing.Rep1N(parsing.Seq(
                    parsing.Capture("r", parsing.Rule('rule')),
                    parsing.Hook('add_rules', [("_", parsing.Node),
                                               ("r", parsing.Node)])
                )),
                parsing.Rule('Base.eof')
            ),

            #
            # rule ::= ns_name : rn "::=" alternatives : alts
            #                             #add_rule(_, rn, alts) ';'
            # ;
            #
            'rule': parsing.Seq(
                parsing.Capture("rn", parsing.Rule('ns_name')),
                parsing.Alt(
                    parsing.Call(parsing.Parser.read_text, "::="),
                    parsing.Error("Expected '::='")
                    ),
                parsing.Capture("alts", parsing.Rule('alternatives')),
                parsing.Hook('add_rule', [("_", parsing.Node),
                                          ("rn", parsing.Node),
                                          ("alts", parsing.Node)]),
                parsing.Alt(
                    parsing.Call(parsing.Parser.read_char, ';'),
                    parsing.Error("Expected ';'")
                    )
            ),

            #
            # alternatives ::= sequences : alt #add_alt(_, alt)
            #                  ['|' sequences : alt
            #                   #add_alt(_, alt) ]*
            # ;
            #
            'alternatives': parsing.Seq(
                parsing.Capture('alt', parsing.Rule('sequences')),
                parsing.Hook('add_alt', [("_", parsing.Node),
                                         ("alt", parsing.Node)]),
                parsing.Rep0N(
                    parsing.Seq(
                        parsing.Call(parsing.Parser.read_char, '|'),
                        parsing.Capture('alt', parsing.Rule('sequences')),
                        parsing.Hook('add_alt',
                                     [("_", parsing.Node),
                                      ("alt", parsing.Node)])
                    )
                )
            ),

            #
            # sequences ::= [ sequence : cla #add_sequences(_, cla) ]+
            #;
            #
            'sequences': parsing.Rep1N(
                parsing.Seq(
                    parsing.Capture('cla', parsing.Rule('sequence')),
                    parsing.Hook('add_sequences',
                                 [("_", parsing.Node),
                                  ("cla", parsing.Node)])
                )
            ),

            #
            # sequence ::= '~'? : neg
            #     [ ns_name : rid #add_ruleclause_name(_, rid)
            #       | Base.string : txt #add_text(_, txt)
            #       | Base.char : begin ".." Base.char : end
            #         #add_range(_, begin, end)
            #       | Base.char : c #add_char(_, c)
            #       | '[' alternatives : subsequence ']'
            #         #add_subsequence(_, subsequence)
            #     ] #add_neg(_, neg)
            #     [repeat : rpt #add_rpt(_, rpt) ]?
            #     [':' Base.id : cpt #add_capture(_, cpt) ]?
            #     | hook : h #add_hook(_, h)
            #     | directive : d sequence : s #add_directive(_, d, s)
            # ;
            #
            'sequence': parsing.Alt(
                parsing.Seq(
                    parsing.Capture(
                        'neg',
                        parsing.RepOptional(
                            parsing.Call(parsing.Parser.read_char, '~'))),
                    parsing.Alt(
                        parsing.Seq(
                            parsing.Capture('rid', parsing.Rule('ns_name')),
                            parsing.Hook('add_ruleclause_name',
                                         [("_", parsing.Node),
                                          ("rid", parsing.Node)])
                        ),
                        parsing.Seq(
                            parsing.Capture('txt',
                                            parsing.Rule('Base.string')),
                            parsing.Hook('add_text',
                                         [("_", parsing.Node),
                                          ("txt", parsing.Node)])
                        ),
                        parsing.Seq(
                            parsing.Capture('begin',
                                            parsing.Rule('Base.char')),
                            parsing.Call(parsing.Parser.read_text, ".."),
                            parsing.Capture('end', parsing.Rule('Base.char')),
                            parsing.Hook('add_range',
                                         [("_", parsing.Node),
                                          ("begin", parsing.Node),
                                          ("end", parsing.Node)])
                        ),
                        parsing.Seq(
                            parsing.Capture('c', parsing.Rule('Base.char')),
                            parsing.Hook('add_char',
                                         [("_", parsing.Node),
                                          ("c", parsing.Node)])
                        ),
                        parsing.Seq(
                            parsing.Call(parsing.Parser.read_char, "["),
                            parsing.Alt(
                                parsing.Capture('subsequence',
                                                parsing.Rule('alternatives')),
                                parsing.Error("Expected sequences")
                                ),
                            parsing.Alt(
                                    parsing.Call(parsing.Parser.read_char, "]"),
                                    parsing.Error("Expected ']'")
                                ),
                            parsing.Hook('add_subsequence',
                                         [("_", parsing.Node),
                                          ("subsequence", parsing.Node)]),
                        )
                    ),
                    parsing.Hook('add_neg', [("_", parsing.Node),
                                             ("neg", parsing.Node)]),
                    parsing.RepOptional(
                        parsing.Seq(
                            parsing.Capture('rpt', parsing.Rule('repeat')),
                            parsing.Hook('add_rpt',
                                         [("_", parsing.Node),
                                          ("rpt", parsing.Node)])
                        )
                    ),
                    parsing.RepOptional(
                        parsing.Seq(
                            parsing.Call(parsing.Parser.read_text, ":"),
                            parsing.Capture('cpt', parsing.Rule('Base.id')),
                            parsing.Hook('add_capture',
                                         [('_', parsing.Node),
                                          ('cpt', parsing.Node)])
                        )
                    )
                ),
                parsing.Seq(
                    parsing.Capture('h', parsing.Rule('hook')),
                    parsing.Hook('add_hook', [('_', parsing.Node),
                                              ('h', parsing.Node)])
                ),
                parsing.Seq(
                    parsing.Capture('d', parsing.Rule('directive')),
                    parsing.Capture('s', parsing.Rule('sequence')),
                    parsing.Hook('add_directive', [('_', parsing.Node),
                                                   ('d', parsing.Node),
                                                   ('s', parsing.Node)])
                )
            ),

            # TODO: add directive hooks
            # ns_name ::= @ignore("null") [ Base.id ['.' Base.id]* ]: rid
            #             #add_ruleclause_name(_, rid)
            # ;
            #
            'ns_name': parsing.Seq(
                parsing.Capture(
                    'rid',
                    parsing.Scope(
                        parsing.Call(parsing.Parser.push_ignore,
                                     parsing.Parser.ignore_null),
                        parsing.Call(parsing.Parser.pop_ignore),
                        parsing.Seq(
                            parsing.Rule('Base.id'),
                            parsing.Rep0N(
                                parsing.Seq(
                                    parsing.Call(parsing.Parser.read_text,
                                                 "."),
                                    parsing.Alt(
                                        parsing.Rule('Base.id'),
                                        parsing.Error("Expected identifier after '.'")
                                        )
                                )
                            )
                        )
                    )
                ),
                parsing.Hook('add_ruleclause_name',
                             [("_", parsing.Node),
                              ("rid", parsing.Node)])
            ),

            #
            # repeat ::= '?' #add_optional(_)
            #          | '*' #add_0N(_)
            #          | '+' #add_1N(_)
            # ;
            #
            'repeat': parsing.Alt(
                parsing.Seq(
                    parsing.Call(parsing.Parser.read_char, '?'),
                    parsing.Hook('add_optional', [("_", parsing.Node)])
                ),
                parsing.Seq(
                    parsing.Call(parsing.Parser.read_char, '*'),
                    parsing.Hook('add_0N', [("_", parsing.Node)])
                ),
                parsing.Seq(
                    parsing.Call(parsing.Parser.read_char, '+'),
                    parsing.Hook('add_1N', [("_", parsing.Node)])
                ),
            ),

            #
            # hook ::= '#' ns_name : n #hook_name(_, n)
            #          ['(' param : p #hook_param(_, p)
            #              [',' param : p #hook_param(_, p)]*
            #           ')']?
            # ;
            #
            'hook': parsing.Seq(
                parsing.Call(parsing.Parser.read_char, '#'),
                parsing.Capture('n', parsing.Rule('ns_name')),
                parsing.Hook('hook_name',
                             [('_', parsing.Node), ('n', parsing.Node)]),
                parsing.RepOptional(
                    parsing.Seq(
                        parsing.Call(parsing.Parser.read_char, '('),
                        parsing.Alt(
                            parsing.Capture('p', parsing.Rule('param')),
                            parsing.Error("Expected parameter")
                            ),
                        parsing.Hook('hook_param', [('_', parsing.Node),
                                                    ('p', parsing.Node)]),
                        parsing.Rep0N(
                            parsing.Seq(
                                parsing.Call(parsing.Parser.read_char, ','),
                                parsing.Alt(
                                    parsing.Capture('p', parsing.Rule('param')),
                                    parsing.Error("Expected parameter")
                                    ),
                                parsing.Hook('hook_param',
                                             [('_', parsing.Node),
                                              ('p', parsing.Node)]),
                            )
                        ),
                        parsing.Alt(
                            parsing.Call(parsing.Parser.read_char, ')'),
                            parsing.Error("Expected ')'")
                            )
                    )
                ),
            ),

            #
            # directive ::= '@' ns_name : n #hook_name(_, n)
            #               ['(' param : p #hook_param(_, p)
            #                   [',' param : p #hook_param(_, p)]*
            #                ')']?
            # ;
            'directive': parsing.Seq(
                parsing.Call(parsing.Parser.read_char, '@'),
                parsing.Capture('n', parsing.Rule('ns_name')),
                parsing.Hook('hook_name', [('_', parsing.Node),
                                           ('n', parsing.Node)]),
                parsing.RepOptional(
                    parsing.Seq(
                        parsing.Call(parsing.Parser.read_char, '('),
                        parsing.Alt(
                            parsing.Capture('p', parsing.Rule('param')),
                            parsing.Error("Expected parameter")
                            ),
                        parsing.Hook('hook_param',
                                     [('_', parsing.Node),
                                      ('p', parsing.Node)]),
                        parsing.Rep0N(
                            parsing.Seq(
                                parsing.Call(parsing.Parser.read_char, ','),
                                parsing.Alt(
                                    parsing.Capture('p', parsing.Rule('param')),
                                    parsing.Error("Expected parameter")
                                    ),
                                parsing.Hook('hook_param',
                                             [('_', parsing.Node),
                                              ('p', parsing.Node)]),
                            )
                        ),
                        parsing.Alt(
                            parsing.Call(parsing.Parser.read_char, ')'),
                            parsing.Error("Expected ')'")
                            )
                    )
                ),
            ),

            #
            # param ::= Base.num :n #param_num(_, n)
            #         | Base.string : s #param_str(_, s)
            #         | Base.char : c #param_char(_, c)
            #         | ns_name : i #param_id(_, i)
            # ;
            #
            'param': parsing.Alt(
                parsing.Seq(
                    parsing.Capture('n', parsing.Rule('Base.num')),
                    parsing.Hook('param_num', [('_', parsing.Node),
                                               ('n', parsing.Node)])
                ),
                parsing.Seq(
                    parsing.Capture('s', parsing.Rule('Base.string')),
                    parsing.Hook('param_str', [('_', parsing.Node),
                                               ('s', parsing.Node)])
                ),
                parsing.Seq(
                    parsing.Capture('c', parsing.Rule('Base.char')),
                    parsing.Hook('param_char', [('_', parsing.Node),
                                                ('c', parsing.Node)])
                ),
                parsing.Seq(
                    parsing.Capture('i', parsing.Rule('ns_name')),
                    parsing.Hook('param_id', [('_', parsing.Node),
                                              ('i', parsing.Node)])
                ),
            ),
        })


@meta.hook(EBNF, "EBNF.add_neg")
def add_neg(self, seq, neg):
    if neg.value:
        seq.parser_tree = parsing.Complement(seq.parser_tree)
    return True


@meta.hook(EBNF, "EBNF.add_ruleclause_name")
def add_ruleclause_name(self, ns_name, rid) -> bool:
    ns_name.value = rid.value
    ns_name.parser_tree = parsing.Rule(ns_name.value)
    return True


@meta.hook(EBNF, "EBNF.add_rules")
def add_rules(self, bnf, r) -> bool:
    bnf[r.rulename] = r.parser_tree
    return True


@meta.hook(EBNF, "EBNF.add_rule")
def add_rule(self, rule, rn, alts) -> bool:
    rule.rulename = rn.value
    rule.parser_tree = alts.parser_tree
    return True


@meta.hook(EBNF, "EBNF.add_sequences")
def add_sequences(self, sequences, cla) -> bool:
    if not hasattr(sequences, 'parser_tree'):
        # forward sublevel of sequence as is
        sequences.parser_tree = cla.parser_tree
    else:
        oldnode = sequences
        if isinstance(oldnode.parser_tree, parsing.Seq):
            oldpt = list(oldnode.parser_tree.ptlist)
        else:
            oldpt = [oldnode.parser_tree]
        oldpt.append(cla.parser_tree)
        sequences.parser_tree = parsing.Seq(*tuple(oldpt))
    return True


@meta.hook(EBNF, "EBNF.add_alt")
def add_alt(self, alternatives, alt) -> bool:
    if not hasattr(alternatives, 'parser_tree'):
        # forward sublevel of alt as is
        if hasattr(alt, 'parser_tree'):
            alternatives.parser_tree = alt.parser_tree
        else:
            alternatives.parser_tree = alt
    else:
        oldnode = alternatives
        if isinstance(oldnode.parser_tree, parsing.Alt):
            oldpt = list(oldnode.parser_tree.ptlist)
        else:
            oldpt = [oldnode.parser_tree]
        oldpt.append(alt.parser_tree)
        alternatives.parser_tree = parsing.Alt(*tuple(oldpt))
    return True


@meta.hook(EBNF, "EBNF.add_char")
def add_char(self, sequence, c):
    sequence.parser_tree = parsing.Call(parsing.Parser.read_char,
                                        c.value.strip("'"))
    return True


@meta.hook(EBNF, "EBNF.add_text")
def add_text(self, sequence, txt):
    sequence.parser_tree = parsing.Call(parsing.Parser.read_text,
                                        txt.value.strip('"'))
    return True


@meta.hook(EBNF, "EBNF.add_range")
def add_range(self, sequence, begin, end):
    sequence.parser_tree = parsing.Call(parsing.Parser.read_range,
                                        begin.value.strip("'"),
                                        end.value.strip("'"))
    return True


@meta.hook(EBNF, "EBNF.add_rpt")
def add_rpt(self, sequence, pt):
    oldnode = sequence
    sequence.parser_tree = pt.functor(oldnode.parser_tree)
    return True


@meta.hook(EBNF, "EBNF.add_capture")
def add_capture(self, sequence, cpt):
    sequence.parser_tree = parsing.Capture(cpt.value, sequence.parser_tree)
    return True


@meta.hook(EBNF, "EBNF.add_subsequence")
def add_subsequence(self, sequence, subsequence):
    sequence.parser_tree = subsequence.parser_tree
    return True


@meta.hook(EBNF, "EBNF.add_optional")
def add_optional(self, repeat):
    repeat.functor = parsing.RepOptional
    return True


@meta.hook(EBNF, "EBNF.add_0N")
def add_0N(self, repeat):
    repeat.functor = parsing.Rep0N
    return True


@meta.hook(EBNF, "EBNF.add_1N")
def add_1N(self, repeat):
    repeat.functor = parsing.Rep1N
    return True


@meta.hook(EBNF, "EBNF.add_hook")
def add_hook(self, sequence, h):
    sequence.parser_tree = parsing.Hook(h.name, h.listparam)
    return True


@meta.hook(EBNF, "EBNF.param_num")
def param_num(self, param, n):
    param.pair = (int(n.value), int)
    return True


@meta.hook(EBNF, "EBNF.param_str")
def param_str(self, param, s):
    param.pair = (s.value.strip('"'), str)
    return True


@meta.hook(EBNF, "EBNF.param_char")
def param_char(self, param, c):
    param.pair = (c.value.strip("'"), str)
    return True


@meta.hook(EBNF, "EBNF.param_id")
def param_id(self, param, i):
    param.pair = (i.value, parsing.Node)
    return True


@meta.hook(EBNF, "EBNF.hook_name")
def hook_name(self, hook, n):
    hook.name = n.value
    hook.listparam = []
    return True


@meta.hook(EBNF, "EBNF.hook_param")
def hook_param(self, hook, p):
    hook.listparam.append(p.pair)
    return True


@meta.hook(EBNF, "EBNF.add_directive")
def add_directive(self, sequence, d, s):
    if d.name not in meta._directives:
        raise TypeError("Unkown directive %s" % d.name)
    the_class = meta._directives[d.name]
    sequence.parser_tree = parsing.Directive(the_class(), d.listparam,
                                             s.parser_tree)
    return True
