from meetai.audio.devices import parse_sources

SAMPLE = (
    "0\talsa_output.pci.analog-stereo.monitor\tmodule-alsa-card.c\ts16le 2ch 48000Hz\tSUSPENDED\n"
    "1\talsa_input.pci.analog-stereo\tmodule-alsa-card.c\ts16le 2ch 44100Hz\tSUSPENDED\n"
)


def test_parse_sources_marks_monitors():
    devs = parse_sources(SAMPLE)
    assert [(d.index, d.is_monitor) for d in devs] == [(0, True), (1, False)]
