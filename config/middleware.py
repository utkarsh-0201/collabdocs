import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Django middleware that logs all HTTP requests with timing and user information.
    
    For each request, logs the HTTP method, path, authenticated user (or 'anonymous'),
    response status code, and elapsed time in milliseconds. This helps with debugging,
    monitoring, and performance analysis of the API.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view callable in the chain.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the HTTP request and log details about the request and response.
        
        Measures the elapsed time from request start to response, and logs:
        - HTTP method (GET, POST, etc.)
        - Request path
        - Authenticated user email/username or 'anonymous'
        - HTTP response status code
        - Elapsed time in milliseconds (with 2 decimal places)
        
        Args:
            request: The HTTP request object.
        
        Returns: The HTTP response object from the next middleware/view.
        """
        start_time = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        user = getattr(request.user, 'email', None) or getattr(request.user, 'username', None) or 'anonymous'
        logger.info(
            'METHOD: %s | PATH: %s | USER: %s | STATUS: %s | TIME: %.2f ms',
            request.method,
            request.path,
            user,
            response.status_code,
            elapsed_ms,
        )
        return response
