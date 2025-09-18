import json as _json
from typing import Any, Dict, Optional
from urllib import error as _error, request as _request


class RequestException(Exception):
    def __init__(self, message: str, *, reason: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.reason = reason


class HTTPError(RequestException):
    def __init__(self, message: str, response: "Response") -> None:
        super().__init__(message)
        self.response = response


class Response:
    def __init__(self, status_code: int, headers: Dict[str, Any], content: bytes) -> None:
        self.status_code = status_code
        self.headers = headers
        self._content = content

    @property
    def text(self) -> str:
        try:
            return self._content.decode("utf-8")
        except UnicodeDecodeError:
            return self._content.decode("utf-8", errors="replace")

    @property
    def content(self) -> bytes:
        return self._content

    def json(self) -> Any:
        if not self._content:
            return {}
        return _json.loads(self.text)

    def raise_for_status(self) -> None:
        if 400 <= self.status_code:
            raise HTTPError(f"HTTP {self.status_code}", self)


def request(method: str, url: str, *, headers: Optional[Dict[str, str]] = None,
            data: Optional[Any] = None, json: Optional[Dict[str, Any]] = None,
            timeout: int = 60) -> Response:
    payload = data
    req_headers = dict(headers or {})

    if json is not None:
        payload = _json.dumps(json).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    elif isinstance(payload, str):
        payload = payload.encode("utf-8")

    req = _request.Request(url, data=payload, headers=req_headers, method=method.upper())
    try:
        with _request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            status = getattr(resp, 'status', resp.getcode())
            return Response(status, dict(resp.headers), content)
    except _error.HTTPError as exc:
        content = exc.read()
        response = Response(exc.code, dict(exc.headers or {}), content)
        raise HTTPError(str(exc), response)
    except _error.URLError as exc:
        raise RequestException(str(exc), reason=exc.reason)


def post(url: str, *, headers: Optional[Dict[str, str]] = None,
         data: Optional[Any] = None, json: Optional[Dict[str, Any]] = None,
         timeout: int = 60) -> Response:
    return request("POST", url, headers=headers, data=data, json=json, timeout=timeout)


def patch(url: str, *, headers: Optional[Dict[str, str]] = None,
          data: Optional[Any] = None, json: Optional[Dict[str, Any]] = None,
          timeout: int = 60) -> Response:
    return request("PATCH", url, headers=headers, data=data, json=json, timeout=timeout)


def get(url: str, *, headers: Optional[Dict[str, str]] = None,
        timeout: int = 60) -> Response:
    return request("GET", url, headers=headers, timeout=timeout)


class exceptions:
    RequestException = RequestException
    HTTPError = HTTPError
