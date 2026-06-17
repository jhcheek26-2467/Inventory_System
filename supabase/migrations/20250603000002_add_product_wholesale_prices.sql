create table product_wholesale_prices (
  product_id bigint not null references products (product_id),
  snapshot_date date not null,
  wholesale_cost_per_unit numeric(10, 4),
  primary key (product_id, snapshot_date)
);
