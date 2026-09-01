from .base import *  # noqa: F401,F403

DEBUG = True

# Gelistirmede tarayicidan API'yi kolay test edebilmek icin browsable API acik.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

CORS_ALLOW_ALL_ORIGINS = True
