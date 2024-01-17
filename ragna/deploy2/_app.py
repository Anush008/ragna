from types import SimpleNamespace
from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

import ragna
from ragna.core import RagnaException

from . import _api as api
from . import _auth
from . import _constants as constants
from . import _ui as ui
from ._session import SessionMiddleware
from ._utils import redirect_response


def make_app(config, *, deploy_api: bool, deploy_ui: bool):
    # FIXME: remove the optional deploy_ui
    app = FastAPI(title="Ragna", version=ragna.__version__)

    # from config
    config = SimpleNamespace(
        authentication=_auth.DummyBasicAuth,
        deploy=SimpleNamespace(
            session_storage_url="",
            token_expires=3600,
            cookie_expires=3600,
        ),
    )

    @app.exception_handler(RagnaException)
    async def ragna_exception_handler(
        request: Request, exc: RagnaException
    ) -> JSONResponse:
        if exc.http_detail is RagnaException.EVENT:
            detail = exc.event
        elif exc.http_detail is RagnaException.MESSAGE:
            detail = str(exc)
        else:
            detail = cast(str, exc.http_detail)
        return JSONResponse(
            status_code=exc.http_status_code,
            content={"error": {"message": detail}},
        )

    app.add_middleware(
        SessionMiddleware, config=config, deploy_api=deploy_api, deploy_ui=deploy_ui
    )

    if deploy_api:
        app.include_router(api.make_router(config), prefix="/api")

    if deploy_ui:
        app.include_router(
            ui.make_router(config), prefix=constants.UI_PREFIX, include_in_schema=False
        )

        # # TODO: Preferably, this would be mounted from the UI router directly.
        # #  Unfortunately, this is currently not possible.
        # #  See https://github.com/tiangolo/fastapi/issues/10180.
        # app.mount(
        #     f"{constants.UI_PREFIX}/static",
        #     StaticFiles(directory=Path(__file__).parent / "static"),
        #     name="static",
        # )

        app.add_middleware(
            CORSMiddleware,
            # FIXME
            allow_origins="http://localhost:31476",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/")
    async def redirect(request: Request) -> Response:
        return redirect_response("/ui" if deploy_ui else "/api/docs", htmx=request)

    @app.get("/version")
    async def version():
        return ragna.__version__

    @app.get("/health")
    async def health():
        return Response(b"", status_code=status.HTTP_200_OK)

    return app
