# Security Policy

## Reporting Security Issues

If you discover a security vulnerability, please email security@example.com with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

**Do not** open public GitHub issues for security vulnerabilities.

## Security Features

### Authentication

- HTTP transport supports bearer token authentication via `MCP_API_KEY`
- STDIO transport is unauthenticated (local development only)

### Rate Limiting

- HTTP endpoints: 100 requests per minute per IP
- Configurable via slowapi

### Input Validation

- All inputs have size limits to prevent DoS
- Pydantic validation on all data models

### CORS Protection

- Default: no origins allowed
- Must explicitly configure trusted origins

### Database Security

- SQLite with WAL mode for concurrency
- Optimistic locking for critical updates
- Parameterized queries (SQLAlchemy ORM)

## Best Practices

1. **Production Deployment**:

   - Always set `MCP_API_KEY` for HTTP transport
   - Configure specific CORS origins (never use `*`)
   - Use HTTPS/TLS for HTTP transport
   - Run with non-root user (Docker does this)

2. **Secrets Management**:

   - Store `MCP_API_KEY` in environment variables
   - Use secrets management (e.g., Docker secrets, Kubernetes secrets)
   - Never commit secrets to git

3. **Network Security**:

   - HTTP transport: use reverse proxy (nginx, Caddy)
   - STDIO transport: local only, no network exposure
   - Consider firewall rules for production

4. **Updates**:
   - Keep dependencies updated (`pip install -U -r requirements.txt`)
   - Monitor security advisories for Python packages
   - Use `requirements.lock` for reproducible builds
