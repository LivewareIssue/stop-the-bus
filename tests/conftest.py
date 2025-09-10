from hypothesis import settings

settings.register_profile("fast", max_examples=10)
settings.register_profile("debug", max_examples=1000)
