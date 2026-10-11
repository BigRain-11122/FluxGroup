#!/usr/bin/env python3
"""council_vote.py - named-vote tally for the 7-seat council (council.md IV.4).

Usage:  python council_vote.py [--major] [--round N] SEAT:VOTE ...
        VOTE: y=yes, n=no, a=abstain   (up to 7 seats)
        --major: heavyweight item (trigger #2/#3/#5) -> pass needs 5/7, else 4/7
        --round N: 1=first round (tie -> revote), 2+=tie again -> escalate CEO
Output: tally + verdict (PASS / FAIL / TIE->revote / TIE2->CEO)
Exit:   0=pass 1=fail 2=tie-revote 3=tie2-CEO 9=usage error
Zero external deps by design (license-unverified voting libs rejected per
R-20260929-gov-3; >=4/7 named majority + tie re-vote per council.md IV.4).
"""
import sys

SEATS = 7


def main(argv):
    major = "--major" in argv
    round_n = 1
    if "--round" in argv:
        i = argv.index("--round")
        round_n = int(argv[i + 1])
        del argv[i:i + 2]
    argv = [a for a in argv if a != "--major"]
    votes = {}
    for a in argv:
        seat, _, v = a.partition(":")
        if v not in ("y", "n", "a") or not seat:
            print("ERR bad vote '%s' (use SEAT:y|n|a)" % a)
            return 9
        votes[seat] = v
    if len(votes) > SEATS:
        print("ERR too many seats: %d" % len(votes))
        return 9
    y = list(votes.values()).count("y")
    n = list(votes.values()).count("n")
    q = list(votes.values()).count("a")
    need = 5 if major else 4
    print("votes y=%d n=%d abstain=%d need=%d/%d%s" % (y, n, q, need, SEATS,
          " [major]" if major else ""))
    if y >= need:
        print("VERDICT: PASS")
        return 0
    if y == n:
        if round_n >= 2:
            print("VERDICT: TIE2 -> escalate to CEO")
            return 3
        print("VERDICT: TIE -> revote one round")
        return 2
    print("VERDICT: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
