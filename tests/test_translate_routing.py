from meetai.translate.routing import ShortPhraseTranslator


class Long:
    def translate(self, text, src_lang, tgt_lang):
        return "long"

    def translate_result(self, text, src_lang, tgt_lang):
        from meetai.translate.base import TranslationResult

        return TranslationResult("long", False)


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


def test_long_models_unsure_flag_is_passed_through():
    assert make(-2.5).translate_result("Ցտեսություն", "hy", "en").confident is False


def test_confident_short_model_answer_is_confident():
    r = make(-0.3).translate_result("Բարև", "hy", "en")
    assert (r.text, r.confident) == ("short", True)
