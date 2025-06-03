from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import re
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware(MiddlewareMixin):
    """Custom middleware for security measures."""
    
    def process_request(self, request):
        """Process the request before it reaches the view."""
        # Add security headers
        request.META['X-Content-Type-Options'] = 'nosniff'
        request.META['X-Frame-Options'] = 'DENY'
        request.META['X-XSS-Protection'] = '1; mode=block'
        request.META['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Check for suspicious patterns in request
        self._check_suspicious_patterns(request)
        
        return None
    
    def process_response(self, request, response):
        """Process the response before it's sent to the client."""
        # Add security headers to response
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; img-src 'self' data: https:; font-src 'self' https://cdnjs.cloudflare.com;"
        
        return response
    
    def _check_suspicious_patterns(self, request):
        """Check for suspicious patterns in the request."""
        # Check for SQL injection attempts
        sql_patterns = [
            r'(\%27)|(\')|(\-\-)|(\%23)|(#)',
            r'((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))',
            r'/\*.*\*/',
            r'exec\s*\(.*\)',
            r'select\s+.*\s+from',
            r'insert\s+.*\s+into',
            r'update\s+.*\s+set',
            r'delete\s+.*\s+from',
            r'drop\s+.*\s+table',
            r'truncate\s+.*\s+table',
        ]
        
        # Check for XSS attempts
        xss_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'onerror=',
            r'onload=',
            r'onclick=',
            r'onmouseover=',
            r'eval\(',
            r'document\.cookie',
            r'document\.write',
        ]
        
        # Check request path
        path = request.path
        for pattern in sql_patterns + xss_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(f'Suspicious pattern detected in request path: {path}')
                return False
        
        # Check request parameters
        for key, value in request.GET.items():
            for pattern in sql_patterns + xss_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    logger.warning(f'Suspicious pattern detected in GET parameter {key}: {value}')
                    return False
        
        for key, value in request.POST.items():
            for pattern in sql_patterns + xss_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    logger.warning(f'Suspicious pattern detected in POST parameter {key}: {value}')
                    return False
        
        return True

class RateLimitMiddleware(MiddlewareMixin):
    """Custom middleware for rate limiting."""
    
    def process_request(self, request):
        """Process the request before it reaches the view."""
        # Skip rate limiting for static files and media
        if request.path.startswith(('/static/', '/media/')):
            return None
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Check rate limit
        if not self._check_rate_limit(ip):
            logger.warning(f'Rate limit exceeded for IP: {ip}')
            return HttpResponse('Rate limit exceeded. Please try again later.', status=429)
        
        return None
    
    def _check_rate_limit(self, ip):
        """Check if the IP has exceeded the rate limit."""
        # TODO: Implement rate limiting logic using Redis or similar
        return True 