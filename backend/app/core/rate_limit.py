from slowapi import Limiter
from slowapi.util import get_remote_address

# Identify clients using their direct IP address.
# Do not trust forwarded IP headers unless a trusted proxy is configured.
limiter = Limiter(
    key_func=get_remote_address,
    headers_enabled=True,
)
