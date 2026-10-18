# Static coupling ranking - coding rule

Frozen with tag `M1_PLAN`.

- **Basis:** the candidate set follows paper Def. III.3 and Sec. III-C-1a (field types of the host class + parameter types of the method).
- **Input:** the host file at `newCommitHash` (`data/sample_ids.csv`) and the method m (signature in the csv).

## Rules

1. **Candidates.** C = declared types of all fields of H union declared types of all parameters of m.
   - Generic container (`List<Foo>`, `Map<K,Foo>`, `Optional<Foo>`, `Foo[]`): use the element type(s) `Foo`.
   - Exclude primitives, `java.*` / `javax.*` types, and H itself.
   - Resolve simple names to FQNs via H's imports or the same package.
2. **Score.** For each T in C, Score(T) = the number of expressions in m's body that access a member (field or method call) through a field, parameter or local variable of type T. Each occurrence counts once.
3. **Ranking.** Rank by score, descending; break ties alphabetically by FQN. Candidates with score 0 stay in C (they count for H2) but rank below any candidate with score > 0.
4. **Static top-1.** The first ranked candidate. If C is empty, record `NONE`.
5. **Recording.** Record each case in `outputs/static/<ref_id>.csv` with these columns: candidate FQN, source (field/param), occurrences (line numbers), score.

## Hybrid and hallucination coding

- **Hybrid:** use the LLM top-1 if it is in C; otherwise use the static top-1.
- **H1:** the LLM's class does not exist in the project at `newCommitHash`. Check with `git ls-tree -r --name-only <commit> | grep "/<SimpleName>.java$"`, and also search for inner or non-public classes with `git grep "class <SimpleName>" <commit>`. Save the command output in `outputs/h_check/<ref_id>.txt`.
- **H2:** the class exists but is not in C.
- **Match with gold:** exact FQN. If the LLM gives a simple name that resolves uniquely in the project, resolve it and record that it was resolved.

## Notes

- Inner-class host (outer class as the target) was not encountered in the 12-case sample.
