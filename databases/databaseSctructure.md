# Users

users (
    id UUID PRIMARY KEY,
    name VARCHAR,
    email VARCHAR UNIQUE,
    password_hash TEXT,
    role ENUM('admin', 'staff', 'validator'),
    university_id UUID,
    created_at TIMESTAMP
)

# Wallets

wallets (
    id UUID PRIMARY KEY,
    user_id UUID,
    wallet_address VARCHAR UNIQUE,
    is_primary BOOLEAN,
    verified BOOLEAN,
    created_at TIMESTAMP
)

# Universities

universities (
    id UUID PRIMARY KEY,
    name VARCHAR,
    accreditation ENUM('A','B','C'),
    wallet_address VARCHAR,
    is_active BOOLEAN,
    created_at TIMESTAMP
)

# Students

students (
    id UUID PRIMARY KEY,
    name VARCHAR,
    nim VARCHAR UNIQUE,
    university_id UUID,
    created_at TIMESTAMP
)

# Diplomas

diplomas (
    id UUID PRIMARY KEY,
    student_id UUID,
    university_id UUID,

    diploma_number VARCHAR,

    ipfs_cid TEXT,
    document_hash VARCHAR,

    tx_hash VARCHAR,
    block_number BIGINT,

    status ENUM('valid','revoked'),

    issued_at TIMESTAMP,
    created_at TIMESTAMP
)

# Transactions

transactions (
    id UUID PRIMARY KEY,

    tx_hash VARCHAR UNIQUE,
    tx_type ENUM(
        'REGISTER_UNIVERSITY',
        'ISSUE_DIPLOMA',
        'VERIFY_DIPLOMA',
        'REVOKE_DIPLOMA',
        'UPDATE_ACCREDITATION'
    ),

    wallet_address VARCHAR,

    status ENUM('pending','success','failed'),

    block_number BIGINT,
    gas_used BIGINT,

    created_at TIMESTAMP
)

# Verification Logs

verification_logs (
    id UUID PRIMARY KEY,
    document_hash VARCHAR,
    result ENUM('valid','invalid'),
    checked_at TIMESTAMP,
    ip_address VARCHAR
)