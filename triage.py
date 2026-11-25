"""Terminal prototype: simulated AI fraud triage with calibrated vs overstated confidence.

The AI here is SIMULATED: its recommendations and confidence scores are preset
in cases.json. The analyst accepts or overrides each recommendation, and the
program logs every decision so reliance can be measured.
"""
import csv
import json
import os
from datetime import datetime

CASES_FILE = "cases.json"
RESULTS_DIR = "results"


def ask(prompt, allowed):
    """Keep asking until the user types one of the allowed answers."""
    while True:
        answer = input(prompt).strip().lower()
        if answer in allowed:
            return answer
        print(f"  Please type one of: {', '.join(allowed)}")


def show_case(case, number, total, confidence):
    print("\n" + "=" * 50)
    print(f"Case {number} of {total}")
    print("=" * 50)
    print(f"  Amount:        £{case['amount_gbp']:.2f}")
    print(f"  Merchant:      {case['merchant']} ({case['category']})")
    print(f"  Country:       {case['country']}")
    print(f"  Time:          {case['time']}")
    print(f"  Card present:  {'yes' if case['card_present'] else 'no'}")
    print("-" * 50)
    print(f"  AI recommends: {case['ai_recommendation'].upper()}")
    print(f"  AI confidence: {confidence * 100:.0f}%")


def other(label):
    return "legitimate" if label == "fraud" else "fraud"


def summarise(rows):
    """Print reliance: how often the analyst followed the AI, split by AI correctness."""
    if not rows:
        print("\nNo decisions recorded.")
        return

    def rate(subset):
        if not subset:
            return "n/a"
        followed = sum(r["followed_ai"] for r in subset)
        return f"{followed}/{len(subset)} ({followed / len(subset):.0%})"

    right = [r for r in rows if r["ai_correct"]]
    wrong = [r for r in rows if not r["ai_correct"]]
    half = len(rows) // 2
    early, late = rows[:half], rows[half:]

    print("\n" + "=" * 50)
    print("SESSION SUMMARY")
    print("=" * 50)
    print(f"  Followed AI when AI was right: {rate(right)}")
    print(f"  Followed AI when AI was wrong: {rate(wrong)}")
    if half:
        print(f"  Followed AI, early cases:      {rate(early)}")
        print(f"  Followed AI, late cases:       {rate(late)}")
    correct = sum(r["analyst_correct"] for r in rows)
    print(f"  Analyst's own accuracy:        {correct}/{len(rows)} ({correct / len(rows):.0%})")

    # Reliance by displayed confidence level: did the analyst follow the AI more
    # as the shown number went up, and was the AI actually right that often?
    print("\n  By displayed confidence (followed AI / AI actually right):")
    for level in sorted({r["confidence_shown"] for r in rows}, reverse=True):
        group = [r for r in rows if r["confidence_shown"] == level]
        followed = sum(r["followed_ai"] for r in group)
        ai_right = sum(r["ai_correct"] for r in group)
        print(f"    {level * 100:>3.0f}% shown: followed {followed}/{len(group)}, "
              f"AI right {ai_right}/{len(group)}")


def main():
    with open(CASES_FILE, encoding="utf-8") as f:
        cases = json.load(f)

    print("SIMULATED AI FRAUD TRIAGE (prototype)")
    print("The AI and all transactions here are simulated.\n")
    mode = ask("Confidence mode - [c]alibrated or [o]verstated? ", ["c", "o"])
    mode = "calibrated" if mode == "c" else "overstated"
    feedback = ask("Show feedback after each decision? [y/n] ", ["y", "n"]) == "y"
    conf_field = f"confidence_{mode}"

    rows = []
    for number, case in enumerate(cases, start=1):
        confidence = case[conf_field]
        show_case(case, number, len(cases), confidence)
        choice = ask("\nAccept AI recommendation [a], override [o], or quit [q]? ", ["a", "o", "q"])
        if choice == "q":
            break

        followed = choice == "a"
        final = case["ai_recommendation"] if followed else other(case["ai_recommendation"])
        analyst_correct = final == case["true_label"]
        rows.append({
            "case_id": case["id"],
            "position": number,
            "mode": mode,
            "feedback_on": feedback,
            "confidence_shown": confidence,
            "ai_recommendation": case["ai_recommendation"],
            "ai_correct": case["ai_correct"],
            "followed_ai": followed,
            "final_decision": final,
            "analyst_correct": analyst_correct,
        })

        if feedback:
            print(f"\n  Feedback: the AI was {'CORRECT' if case['ai_correct'] else 'WRONG'}. "
                  f"Your decision was {'CORRECT' if analyst_correct else 'WRONG'} "
                  f"(true label: {case['true_label']}).")

    summarise(rows)

    if rows:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(RESULTS_DIR, f"session_{mode}_{stamp}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nDecisions saved to {path}")


if __name__ == "__main__":
    main()