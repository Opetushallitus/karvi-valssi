from __future__ import absolute_import

from functools import wraps

from django_ratelimit import ALL, UNSAFE
from django_ratelimit.exceptions import Ratelimited
from django_ratelimit.core import is_ratelimited


def custom_ratelimit(group_prefix=None, rate=None, method=ALL, block=True):
    def decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kw):
            old_limited = getattr(request, 'limited', False)
            user_ip = ratelimit_ip_key(None, request)
            group = f"{group_prefix}_{user_ip}"
            ratelimited = is_ratelimited(request=request, group=group, fn=fn,
                                         key=ratelimit_ip_key, rate=rate, method=method,
                                         increment=True)
            request.limited = ratelimited or old_limited
            if ratelimited and block:
                raise Ratelimited()
            return fn(request, *args, **kw)
        return _wrapped
    return decorator


custom_ratelimit.ALL = ALL
custom_ratelimit.UNSAFE = UNSAFE


def ratelimit_ip_key(group, request):
    return request.META.get("HTTP_X_REAL_IP", request.META["REMOTE_ADDR"])
