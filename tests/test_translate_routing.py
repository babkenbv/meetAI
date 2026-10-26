from meetai.translate.routing import ShortPhraseTranslator


class Long:
    def translate(self, text, src_lang, tgt_lang):
        return "long"


class Short:
    def __init__(self, confidence):
        self.confidence = confidence

    def translate_scored(self, text, src_lang, tgt_lang):
        return "short", self.confidence


def make(confidence, **kw):
    return ShortPhraseTranslator(Short(confidence), Long(), **kw)


def test_confident_one_word_goes_to_short_model():
    assert make(-0.3).translate("Բարև", "hy", "en") == "short"


def test_unsure_short_model_falls_back_to_long_model():
    assert make(-2.5).translate("Ցտեսություն", "hy", "en") == "long"


def test_two_words_go_to_long_model_by_default():
    assert make(-0.1).translate("Իսկ դուք", "hy", "en") == "long"


def test_max_words_is_configurable():
    assert make(-0.1, max_words=2).translate("Իսկ դուք", "hy", "en") == "short"
