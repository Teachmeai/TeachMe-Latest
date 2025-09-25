#!/usr/bin/env python3
"""
Decode (and optionally verify) a JWT.

Usage:
  python scripts/decode_jwt.py [--token <JWT>] [--secret <SECRET>] [--alg HS256] [--no-verify]

Notes:
  - If --token is omitted, a built-in SAMPLE_TOKEN will be used (for quick testing).

Environment variables (fallbacks):
  JWT_SECRET        Secret used to verify HS* tokens (default: built-in)
  JWT_ALGORITHM     Algorithm (default: HS256)

Examples:
  # Verify using env JWT_SECRET
  JWT_SECRET=supersecret python scripts/decode_jwt.py --token "$TOKEN"

  # Decode without verification (for debugging only)
  python scripts/decode_jwt.py --token "$TOKEN" --no-verify

  # Use built-in sample token and built-in secret
  python scripts/decode_jwt.py

  # Provide secret and algorithm explicitly
  python scripts/decode_jwt.py --token "$TOKEN" --secret supersecret --alg HS256
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone

import jwt

# Hardcoded fallbacks (requested)
# NOTE: CLI args and environment variables still take precedence.
DEFAULT_SECRET = "U7NLLmdCpn7hiQYa+2JPWW7Iq2KSr8CG3COuLm6IMC9bqqjObiJBjACX3EMI2iceKkhHPPnLfkUo9LOq8lfX9w=="
DEFAULT_ALG = "HS256"
# Single-line built-in token variable (requested)
tiken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1ZWRlOWZlZS0wNGQxLTQyNTAtODE3Ny05YzFmNjMwOWJkMDQiLCJhY3RpdmVfcm9sZSI6InN1cGVyX2FkbWluIiwiaWF0IjoxNzU4NjM4NzA0LCJleHAiOjE3NTg3MjUxMDQsImF1ZCI6ImFnZW50IiwiaXNzIjoidGVhY2htZS1iYWNrZW5kIn0.xosRuV6mn6Pp9_1rlYTzwS3Bm-TYKDxc-Ehz8csZcoc"


def b64url_decode(segment: str) -> bytes:
    segment += '=' * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment.encode('utf-8'))


def human_time(ts: int | float | None) -> str:
    if ts is None:
        return "-"
    try:
        dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        return dt.isoformat()
    except Exception:
        return str(ts)


def pretty(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Decode and optionally verify a JWT")
    parser.add_argument('--token', required=False, help='JWT to decode (defaults to built-in tiken)')
    parser.add_argument('--secret', default=os.getenv('JWT_SECRET', DEFAULT_SECRET), help='Secret for HS* verification (env JWT_SECRET)')
    parser.add_argument('--alg', default=os.getenv('JWT_ALGORITHM', DEFAULT_ALG), help='Algorithm (default HS256)')
    parser.add_argument('--no-verify', action='store_true', help='Decode without signature/claims verification')
    args = parser.parse_args()

    token = (args.token or tiken).strip()
    if not args.token:
        print('[info] Using built-in tiken (omit --token to use your own).')

    # Split token
    try:
        header_b64, payload_b64, signature_b64 = token.split('.')
    except ValueError:
        print('Invalid JWT format (expected 3 segments separated by dots).', file=sys.stderr)
        return 1

    # Raw parts
    try:
        raw_header = json.loads(b64url_decode(header_b64))
    except Exception:
        raw_header = {'_decode_error': 'invalid header'}
    try:
        raw_payload = json.loads(b64url_decode(payload_b64))
    except Exception:
        raw_payload = {'_decode_error': 'invalid payload'}

    print('=== Raw Segments ===')
    print('Header:', pretty(raw_header))
    print('Payload:', pretty(raw_payload))
    print('Signature (base64url):', signature_b64)
    print()

    # Human-friendly time fields
    print('=== Time Fields (human) ===')
    for k in ('iat', 'nbf', 'exp'):
        v = raw_payload.get(k)
        print(f'{k}:', v, '->', human_time(v))
    print()

    if args.no_verify:
        print('Verification skipped (--no-verify).')
        return 0

    # Verification
    if not args.secret:
        print('Missing secret for verification. Provide --secret or set JWT_SECRET, or use --no-verify.', file=sys.stderr)
        return 2

    try:
        decoded = jwt.decode(
            token,
            key=args.secret,
            algorithms=[args.alg],
            options={
                'verify_signature': True,
                'verify_exp': True,
                'verify_iat': False,
                'verify_nbf': True,
            },
            audience=raw_payload.get('aud'),  # if present, enforce
            issuer=raw_payload.get('iss'),    # if present, enforce
        )
        print('=== Verified Claims ===')
        print(pretty(decoded))
        return 0
    except Exception as e:
        print('Verification failed:', str(e), file=sys.stderr)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())


