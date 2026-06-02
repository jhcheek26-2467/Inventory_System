-- Milestone 1: core inventory schema (matches existing Supabase tables)

create table distributors (
  distributor_id bigserial primary key,
  distributor_name text unique not null
);

create table categories (
  category_id bigserial primary key,
  category_name text unique not null
);

create table products (
  product_id bigserial primary key,
  product_name text not null,
  product_code text,
  bin_number text,
  container_size_ml integer,
  distributor_id bigint references distributors (distributor_id),
  category_id bigint references categories (category_id),
  wholesale_cost_per_unit numeric(10, 4),
  avg_retail_price_per_serving numeric(10, 2)
);

create table locations (
  location_id bigserial primary key,
  location_name text unique not null
);

create table inventory_snapshots (
  snapshot_id bigserial primary key,
  snapshot_date date not null,
  product_id bigint references products (product_id),
  location_id bigint references locations (location_id),
  quantity numeric(10, 2) not null default 0
);

insert into locations (location_name)
values
  ('Circle Bar'),
  ('Main Bar'),
  ('Garage Bar'),
  ('Ice Bar'),
  ('Rooftop Bar'),
  ('Jungle Bar'),
  ('Dry Storage'),
  ('VIP'),
  ('BIBs'),
  ('DO NOT TOUCH');
