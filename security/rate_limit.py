import time
from collections import defaultdict, deque


MAX_REQUESTS = 5
WINDOW_SECONDS = 60


_request_history = defaultdict(deque)


def check_rate_limit(identity: str) -> None:
    """
    Allow a limited number of requests for each identity.
    """

    if not identity:
        raise ValueError(
            "Rate-limit identity is required."
        )

    current_time = time.time()

    request_times = _request_history[identity]

    # Remove expired requests.
    while request_times:

        oldest_request = request_times[0]

        if (
            current_time - oldest_request
            >= WINDOW_SECONDS
        ):
            request_times.popleft()

        else:
            break

    # Reject if the limit has been reached.
    if len(request_times) >= MAX_REQUESTS:

        raise PermissionError(
            f"Rate limit exceeded. Maximum "
            f"{MAX_REQUESTS} requests are allowed "
            f"within {WINDOW_SECONDS} seconds."
        )

    # Record this request.
    request_times.append(
        current_time
    )


def reset_rate_limit(identity: str) -> None:
    """
    Reset the rate-limit history for one identity.
    """

    _request_history.pop(
        identity,
        None,
    )


def reset_all_rate_limits() -> None:
    """
    Reset all rate-limit histories.
    """

    _request_history.clear()