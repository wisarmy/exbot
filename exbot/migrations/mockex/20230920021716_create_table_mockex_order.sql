-- Add migration script here
create table if not exists mockex_orders (
    id uuid primary key not null,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    qty INTEGER NOT NULL, 
    side TEXT NOT NULL,
    reduce_only BOOLEAN NOT NULL,
    created INTEGER NOT NULL DEFAULT 0,
    updated INTEGER NOT NULL DEFAULT 0
);

create table if not exists mockex_positions (
    id uuid primary key not null,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    qty REAL NOT NULL,
    side TEXT NOT NULL,
    created INTEGER NOT NULL DEFAULT 0,
    updated INTEGER NOT NULL DEFAULT 0
);

