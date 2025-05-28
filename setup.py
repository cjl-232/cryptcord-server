import sqlite3

# For true security here, I think we need a separate set of keys for key exchange.
# Issue is this. Someone takes control of the server -> they can change any 'voting' system freely. Or applicant lists, for that matter.
# Perhaps it's best to avoid all applicants altogether. Instead, send 

# Focusing on DMs for now. How to actually find someone?
# Select a public key, database searches for it, returns the person. Client posts them
# an intro encrypted with their public RSA key. Receiver then needs that to decrypt it and to
# sign a reply. If someone modifies the client program so they can 'log in' with just the public signature/RSA keys,
# the original sender's client will still flag any response or further messages
#  they get as being invalid!

DB_NAME = 'database2.db'
with sqlite3.connect(DB_NAME) as connection:
    cursor = connection.cursor()
    cursor.execute(
        (
            'CREATE TABLE IF NOT EXISTS users('
            '   id INTEGER PRIMARY KEY,'
            '   public_key BYTEA UNIQUE NOT NULL'
            ')'
        ),
    )
    cursor.execute(
        (
            'CREATE INDEX IF NOT EXISTS users_public_key_index '
            'ON users(public_key)'
        ),
    )
    cursor.execute(
        (
            'CREATE TABLE IF NOT EXISTS direct_messages('
            '   id INTEGER PRIMARY KEY,'
            '   receiver_id INTEGER NOT NULL,'
            '   sender_id INTEGER NOT NULL,'
            '   encrypted_message BYTEA NOT NULL,'
            '   signature BYTEA NOT NULL,'
            '   FOREIGN KEY(receiver_id) REFERENCES users(id),'
            '   FOREIGN KEY(sender_id) REFERENCES users(id)'
            ')'
        ),
    )
    cursor.execute(
        (
            'CREATE INDEX IF NOT EXISTS direct_messages_user_pair_index '
            'ON direct_messages(receiver_id, sender_id)'
        ),
    )

    # When user logs in, retrieve any requests with no confirmed message exchanges (filter the second part on the client side).
    # Match the signatures to existing file. If acceptable, generate an exchange key in response, derive fernet, sign own x, send.
    # Original sender then derives their own fernet. Note that their X key needs to be stored locally while the request is outstanding.
    # After a verified response (in a yaml file, have the private x key and recipient's public verification key paths stored), replace x with a path
    # to a generated fernet key serialisation
    # AVOID deleting these from the table. Would only add complications.
    cursor.execute(
        (
            'CREATE TABLE IF NOT EXISTS direct_message_requests('
            '   id INTEGER PRIMARY KEY,'
            '   receiver_id INTEGER NOT NULL,'
            '   sender_id INTEGER NOT NULL,'
            '   sender_exchange_key BYTEA NOT NULL,'
            '   sender_exchange_key_signature BYTEA NOT NULL,'
            '   receiver_exchange_key BYTEA, -- set to null initially'
            '   receiver_exchange_key_signature BYTEA,'
            '   FOREIGN KEY(receiver_id) REFERENCES users(id),'
            '   FOREIGN KEY(sender_id) REFERENCES users(id)'
            ')'
        ),
    )


    cursor.execute(
        (
            'CREATE TABLE IF NOT EXISTS groups('
            '   id INTEGER PRIMARY KEY,'
            '   public_key BYTEA UNIQUE NOT NULL,'
            '   handle VARCHAR(255) UNIQUE NOT NULL'
            ')'
        ),
    )
    cursor.execute(
        (
            'CREATE TABLE IF NOT EXISTS members('
            '   id INTEGER PRIMARY KEY,'
            '   public_key BYTEA UNIQUE NOT NULL,'
            '   handle VARCHAR(255) UNIQUE NOT NULL'
            ')'
        ),
    )
    cursor.execute(
        (
            'CREATE INDEX IF NOT EXISTS public_key_index '
            'ON members (public_key)'
        ),
    )
    cursor.execute(
        (
            'CREATE TABLE IF NOT EXISTS applicants('
            '   id INTEGER PRIMARY KEY,'
            '   public_key BYTEA UNIQUE NOT NULL,'
            '   verifiable_greeting BYTEA NOT NULL'
            ')'
        ),
    )
    cursor.execute(
        (
            'CREATE TABLE IF NOT EXISTS application_votes('
            '   id INTEGER PRIMARY KEY,'
            '   member_id INTEGER NOT NULL,'
            '   applicant_id INTEGER NOT NULL,'
            '   FOREIGN KEY(member_id) REFERENCES members(id),'
            '   FOREIGN KEY(applicant_id) REFERENCES applicants(id),'
            '   UNIQUE(member_id, applicant_id)'
            ')'
        ),
    )