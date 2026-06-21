"""Service layer: STT, agent, TTS, and supporting utilities.

Each service is an interface with an offline **stub** implementation so the
backend runs without a GPU or external API keys. Real implementations land in
their own TDDs (STT=01, agent=02/03/04, TTS=05) behind the same interface.
"""
