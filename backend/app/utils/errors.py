from fastapi import Request
from fastapi.responses import JSONResponse


async def http_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    status = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "Unexpected error")
    return JSONResponse(status_code=status, content={"error": {"message": detail, "status": status}})
