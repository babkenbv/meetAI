from meetai.translate.routing import ShortPhraseTranslator


class Named:
    def __init__(self, name):
        self.name = name

    def translate(self, text, src_lang, tgt_lang):
        return self.name


def test_short_inputs_go_to_short_model():
    t = ShortPhraseTranslator(Named("short"), Named("long"), max_words=2)
    assert t.translate("Բարև", "hy", "en") == "short"
    assert t.translate("Ինչպե՞ս ես", "hy", "en") == "short"


def test_longer_inputs_go_to_long_model():
    t = ShortPhraseTranslator(Named("short"), Named("long"), max_words=2)
    assert t.translate("Լավ եմ շնորհակալություն", "hy", "en") == "long"
