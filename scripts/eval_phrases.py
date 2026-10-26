"""Score short-phrase translation: OPUS-MT, NLLB, and the routed combination used by the app.

The 26 phrases and their acceptable English (a regex each) are the author's own labels of everyday Armenian, not an
external gold set: treat the numbers as indicative. Usage: python scripts/eval_phrases.py
"""

import re

from meetai.config import Config
from meetai.translate.nllb_ct2 import NllbTranslator
from meetai.translate.opus_ct2 import OpusHyEnTranslator
from meetai.translate.routing import ShortPhraseTranslator

P = [
 ("Բարև","^(hi|hello|hey)\\b"),("Ողջույն","^(hi|hello|greetings)\\b"),("Բարի լույս","good morning"),("Բարի երեկո","good evening"),
 ("Բարի գիշեր","good night"),("Շնորհակալություն","thank"),("Խնդրեմ","welcome|please|here you"),("Ներեցեք","sorry|excuse|forgive|pardon"),
 ("Կներեք","sorry|excuse|forgive|pardon"),("Այո","^yes"),("Ոչ","^no\\b"),("Լավ","^(good|ok|okay|fine|well|all right|alright)"),
 ("Լավ եմ","(i'm|i am) (fine|good|well|ok|okay|all right)"),("Ինչպես ես","how are you"),("Ինչպե՞ս ես","how are you"),("Ինչպես եք","how are you"),
 ("Իսկ դուք","(what|how) about you|and you\\??$"),("Իսկ դու","(what|how) about you|and you\\??$"),("Ցտեսություն","bye|see you"),
 ("Չգիտեմ","don't know|do not know"),("Հասկանում եմ","understand"),("Չեմ հասկանում","(don't|do not|can't|cannot) understand"),
 ("Խնդրում եմ","please|i ask|i beg|you're welcome"),("Ինչու՞","^why"),("Ինչ է քո անունը","name"),("Շատ լավ","very (good|well|nice)|great|excellent"),
]


def main() -> None:
    c = Config()
    nllb = NllbTranslator(c.translation_model, c.translation_tokenizer)
    opus = OpusHyEnTranslator(c.translation_short_model)
    routed = ShortPhraseTranslator(opus, nllb, c.short_max_words, c.short_min_confidence)
    systems = {"OPUS": opus, "NLLB": nllb, "routed (app)": routed}
    for s in systems.values():
        s.translate("\u0532\u0561\u0580\u0587", "hy", "en")
    ok = {name: 0 for name in systems}
    for hy, rx in P:
        outs = {name: s.translate(hy, "hy", "en") for name, s in systems.items()}
        for name, out in outs.items():
            ok[name] += bool(re.search(rx, out, re.I))
        print(f"{hy:18s} " + " | ".join(f"{'ok ' if re.search(rx, o, re.I) else 'BAD'} {o[:22]:22s}" for o in outs.values()))
    print("\n" + ", ".join(f"{name}: {n}/{len(P)}" for name, n in ok.items()))


if __name__ == "__main__":
    main()
