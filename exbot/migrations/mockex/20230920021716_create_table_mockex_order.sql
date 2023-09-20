-- Add migration script here
create table if not exists mockex_orders (
    id uuid primary key not null,
    price REAL NOT NULL,
    qty INTEGER NOT NULL, 
    side TEXT NOT NULL,
    reduce_only BOOLEAN NOT NULL,
    created INTEGER NOT NULL DEFAULT 0,
    updated INTEGER NOT NULL DEFAULT 0
);
