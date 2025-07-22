# Cryptcord Server

A FastAPI-based lightweight API to facilitate the exchange of encrypted
messages and the derivation of shared symmetric keys. Intended for use with
suitable clients that can automatically handle encryption and authentication,
such as:

* [Cryptcord Client](https://github.com/cjl232-redux/cryptcord-client)
* [Cursecord](https://github.com/cjl232-redux/cursecord)

## Basics

This system is designed around the use of elliptic curve digital signature
algorithms and Diffie-Hellman key exchange. Users need to have a long-term
32-byte private-public key pair, the public component of which must be known
to prospective contacts. In general, it is recommended that a Curve25519 key
pair is used.

## Making Requests

Five endpoints are provided with this API. Wherever the request body includes
byte strings (such as the bytes of a public key or signature, or a message
encrypted with a Fernet key), these should be provided in a Base64-encoded
form with appropriate padding.

### Docs

Located at /docs, this endpoint contains a standard webpage with automatically
generated documentation for all other endpoints.

### Ping

Located at /ping, this endpoint accepts GET requests and returns a minimal
'pong' response.

### Fetch

Located at /data/fetch, this endpoint accepts POST requests. The request body
must contain the user's long-term public key. To reduce the size of responses,
it may optionally include a list of public keys from which the user is willing
to accept data and a minimum datetime, filtering out data stored on the server
by other users before that point. A successful request will return a list of
retrieved exchange keys and a list of retrieved messages. Each element will
include the data itself, a signature for verification, and the timestamp
created when the data was posted. Message elements will also include a unique
16-byte hexadecimal identifier, while exchange key elements *may* also include
the public exchange key they were sent in response to, if applicable.

### Post Exchange Key

Located at /data/post/exchange-key, this endpoint accepts POST requests. The
request body must contain the user's long-term public key, the long-term public
key of the desired recipient, a 32-byte public key belonging to an exchange
key pair, and a 64-byte signature allowing the recipient to verify the public
exchange key. If the exchange key is being sent in response to a previously
received public exchange key, the body should also include that key so the
original sender can easily automate derivation of the same shared secret. A 
successful request will return metadata containing a timestamp.

### Post Message

Located at /data/post/message, this endpoint accepts POST requests. The
request body must contain the user's long-term public key, the long-term public
key of the desired recipient, a Base64-encoded message, and a 64-byte signature
allowing the recipient to authenticate the message. The maximum accepted
message length is dependent on server settings, but defaults to 2,764,
corresponding to approximately 2,000 plaintext characters if Fernet encryption
is used. A successful request will return metadata containing a timestamp and
a unique 16-byte hexadecimal identifier for the stored message.

## Security & Authentication

By design, no significant authentication or encryption is performed within
the API - the intention is that clients have no need to trust that the server
itself is secure. This means that in principle any user can request the data
addressed to any public key regardless of whether they have the associated
private key. Similarly, when posting data, users can provide any public key
of their choosing in place of their own, and the server will store the data
even if the signature provided alongside it is invalid[^1]. As a result,
users should treat **all** retrieved data as unauthenticated and assume **any**
posted data will be publicly exposed. Security must therefore be provided on
the client side:

* Any posted messages should be encrypted, ideally using a shared symmetric
  key derived from a Diffie-Hellman key exchange.
* Any posted public exchange keys should belong to ephemeral key pairs
  generated and used for that exchange only, ideally using Curve25519.
* All retrieved data should be authenticated against the provided public key.

Provided the user knows with certainty that the public key owned by a contact
belongs exclusively to them, and reliable encryption algorithms are used,
messages exchanged using this API are secure against any attacks available to
non-quantum computers even if the server is compromised.


[^1]: An optional setting does exist to have the server authenticate posted
  data. However, this is intended as a tool for the server owner to control
  data storage, and users should assume it is disabled.