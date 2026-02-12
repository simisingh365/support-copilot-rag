# API Rate Limits

## Overview

To ensure fair usage and maintain optimal performance for all users, our API implements rate limiting. This document explains our rate limit policies, how they work, and best practices for handling rate limits in your application.

## Rate Limit Tiers

Rate limits vary based on your subscription tier:

### Free Tier
- **Requests per minute**: 10
- **Requests per day**: 1,000
- **Burst allowance**: 15 requests

### Starter Tier
- **Requests per minute**: 100
- **Requests per day**: 50,000
- **Burst allowance**: 150 requests

### Professional Tier
- **Requests per minute**: 500
- **Requests per day**: 500,000
- **Burst allowance**: 750 requests

### Enterprise Tier
- **Requests per minute**: Custom (typically 1,000+)
- **Requests per day**: Unlimited
- **Burst allowance**: Custom

## Rate Limit Headers

Every API response includes headers that provide information about your current rate limit status:

- `X-RateLimit-Limit`: Your maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in the current minute
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets
- `X-RateLimit-Used`: Number of requests used in the current minute

Example response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1678901234
X-RateLimit-Used: 13
```

## Rate Limit Responses

When you exceed your rate limit, you will receive a `429 Too Many Requests` response:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please retry after 30 seconds.",
  "retry_after": 30
}
```

The `retry_after` value indicates how many seconds to wait before making another request.

## Handling Rate Limits

### Exponential Backoff

Implement exponential backoff when handling rate limit errors:

```python
import time
import requests

def make_request_with_backoff(url, max_retries=5):
    for attempt in range(max_retries):
        response = requests.get(url)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('retry_after', 30))
            wait_time = min(retry_after * (2 ** attempt), 60)
            time.sleep(wait_time)
        else:
            return response
    
    return None
```

### Request Queuing

For applications with high request volumes, implement a request queue:

```python
import queue
import threading

request_queue = queue.Queue()

def worker():
    while True:
        url = request_queue.get()
        make_request_with_backoff(url)
        request_queue.task_done()

# Start multiple worker threads
for _ in range(5):
    threading.Thread(target=worker, daemon=True).start()
```

### Rate Limit Monitoring

Monitor your rate limit usage to proactively manage your requests:

```python
def check_rate_limit(response):
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    limit = int(response.headers.get('X-RateLimit-Limit', 1))
    
    usage_percent = (1 - remaining / limit) * 100
    
    if usage_percent > 80:
        print(f"Warning: Rate limit usage at {usage_percent:.1f}%")
```

## Best Practices

1. **Cache Responses**: Cache API responses when possible to reduce unnecessary requests
2. **Batch Requests**: Combine multiple operations into single requests when available
3. **Use Webhooks**: Set up webhooks for real-time updates instead of polling
4. **Monitor Usage**: Regularly review your API usage patterns
5. **Plan for Growth**: Choose a tier that accommodates your expected growth

## Increasing Your Rate Limit

If you consistently hit your rate limits, consider:

1. **Upgrading Your Plan**: Higher tiers offer increased rate limits
2. **Contacting Sales**: For custom rate limit requirements, contact our sales team
3. **Optimizing Your Code**: Review your implementation for optimization opportunities

## Rate Limit Exceptions

Certain endpoints may have different rate limits:

- **Authentication endpoints**: Stricter limits to prevent brute force attacks
- **Webhook endpoints**: Higher limits for event delivery
- **Bulk operations**: Special limits for batch processing

Check the specific endpoint documentation for any rate limit variations.

## Testing Rate Limits

When testing your application, use our sandbox environment which has relaxed rate limits:

- Sandbox rate limit: 1,000 requests per minute
- No daily limit in sandbox
- Perfect for development and testing

## Contact Support

If you have questions about rate limits or need assistance optimizing your API usage, contact our support team:

- Email: support@example.com
- Documentation: https://docs.example.com/rate-limits
- Community Forum: https://community.example.com
