from typing import Any, Optional

RsaSigner: Any
RsaVerifier: Any
CLOCK_SKEW_SECS: int
AUTH_TOKEN_LIFETIME_SECS: int
MAX_TOKEN_LIFETIME_SECS: int
logger: Any

class AppIdentityError(Exception): ...

OpenSSLSigner: Any
OpenSSLVerifier: Any
pkcs12_key_as_pem: Any
PyCryptoSigner: Any
PyCryptoVerifier: Any
Signer = OpenSSLSigner
Verifier = OpenSSLVerifier
Signer = PyCryptoSigner
Verifier = PyCryptoVerifier
Signer = RsaSigner
Verifier = RsaVerifier

def make_signed_jwt(signer: Any, payload: Any, key_id: Optional[Any] = ...): ...
def verify_signed_jwt_with_certs(jwt: Any, certs: Any, audience: Optional[Any] = ...): ...
