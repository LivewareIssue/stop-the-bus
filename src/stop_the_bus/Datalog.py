from collections import defaultdict
from dataclasses import dataclass

from stop_the_bus.Card import Rank, Suit

type Var = str
type Const = Rank | Suit | int
type Term = Var | Const


@dataclass(frozen=True, slots=True)
class Atom:
    name: str
    args: tuple[Term, ...]


@dataclass(frozen=True, slots=True)
class Inequality:
    left: Term
    right: Term


type Literal = Atom | Inequality


@dataclass(frozen=True, slots=True)
class Rule:
    head: Atom
    body: tuple[Literal, ...]


type Fact = tuple[Const, ...]
type Predicate = tuple[str, int]
type Relation = set[Fact]
type Database = defaultdict[Predicate, Relation]
type Subst = dict[Var, Const]


def unify(subst: Subst, atom: Atom, fact: Fact) -> bool:
    if len(atom.args) != len(fact):
        return False

    for arg, const in zip(atom.args, fact, strict=True):
        if isinstance(arg, str):
            if arg in subst:
                if subst[arg] != const:
                    return False
            else:
                subst[arg] = const
        elif arg != const:
            return False

    return True


def resolve(subst: Subst, term: Term) -> Const | Var:
    return subst[term] if isinstance(term, str) and term in subst else term


def match(db: Database, subst: Subst, literal: Literal) -> list[Subst]:
    if isinstance(literal, Inequality):
        left = resolve(subst, literal.left)
        right = resolve(subst, literal.right)

        if isinstance(left, str) and isinstance(right, str) and left == right:
            return []

        if not (isinstance(left, str) or isinstance(right, str)):
            return [subst] if left != right else []

        return [subst]

    predicate: Predicate = (literal.name, len(literal.args))
    if predicate not in db:
        return []

    results: list[Subst] = []
    for fact in db[predicate]:
        local_subst: Subst = subst.copy()
        if unify(local_subst, literal, fact):
            results.append(local_subst)

    return results


def solve(db: Database, atoms: tuple[Literal, ...]) -> list[Subst]:
    envs: list[Subst] = [{}]

    for atom in atoms:
        new_envs: list[Subst] = []
        for env in envs:
            new_envs.extend(match(db, env, atom))
        envs = new_envs

    return envs


def instantiate(subst: Subst, atom: Atom) -> Fact | None:
    args: list[Const] = []

    for arg in atom.args:
        if isinstance(arg, str):
            if arg in subst:
                args.append(subst[arg])
            else:
                return None
        else:
            args.append(arg)

    return tuple(args)


def derive(db: Database, rule: Rule) -> set[tuple[Predicate, Fact]]:
    results: set[tuple[Predicate, Fact]] = set()
    predicate: Predicate = (rule.head.name, len(rule.head.args))
    for subst in solve(db, rule.body):
        fact = instantiate(subst, rule.head)
        if fact is not None:
            results.add((predicate, fact))

    return results


def naive_fixpoint(db: Database, rules: list[Rule]) -> None:
    while True:
        added = False
        for rule in rules:
            for predicate, fact in derive(db, rule):
                if fact not in db[predicate]:
                    db[predicate].add(fact)
                    added = True
        if not added:
            break


def query(db: Database, q: Rule) -> list[Subst]:
    db_copy = db.copy()
    naive_fixpoint(db_copy, [q])
    return match(db_copy, {}, q.head)
