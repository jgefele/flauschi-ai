import logging
import os
from typing import Callable

import langchain_core.callbacks
import langfuse
import langfuse.langchain
from wrapt import wrap_function_wrapper

logger = logging.getLogger(__name__)


# taken from openinference.instrumentation.langchain
# this way we don't have to inject the callback into every invoke/stream/...
def auto_instrument(callback: langfuse.langchain.CallbackHandler):
    class _BaseCallbackManagerInit:
        __slots__ = ("_callback",)  # pyright: ignore[reportUnannotatedClassAttribute]
        _callback: langfuse.langchain.CallbackHandler

        def __init__(self, callback: langfuse.langchain.CallbackHandler):
            self._callback = callback

        def __call__(
            self,
            wrapped: Callable[..., None],
            instance: langchain_core.callbacks.BaseCallbackManager,
            args,  # pyright: ignore[reportMissingParameterType]
            kwargs,  # pyright: ignore[reportMissingParameterType]
        ) -> None:
            wrapped(*args, **kwargs)
            for handler in instance.inheritable_handlers:
                # Handlers may be copied when new managers are created, so we
                # don't want to keep adding. E.g. see the following location.
                # https://github.com/langchain-ai/langchain/blob/5c2538b9f7fb64afed2a918b621d9d8681c7ae32/libs/core/langchain_core/callbacks/manager.py#L1876  # noqa: E501
                if isinstance(handler, type(self._callback)):
                    break
            else:
                instance.add_handler(self._callback, True)

    wrap_function_wrapper(
        "langchain_core.callbacks",
        "BaseCallbackManager.__init__",
        _BaseCallbackManagerInit(callback),
    )


def setup_telemetry():
    if not "LANGFUSE_SECRET_KEY" in os.environ:
        logger.info("instrumentation disabled (LANGFUSE_SECRET_KEY not set)")
        return

    langfuse_client = langfuse.get_client()
    if not langfuse_client.auth_check():
        logger.warning("instrumentation disabled (lang)")
        return

    langfuse_handler = langfuse.langchain.CallbackHandler()
    auto_instrument(langfuse_handler)
