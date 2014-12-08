CREATE INDEX
   customer_index
ON
   store_sales (ss_customer_sk) include (ss_sold_date_sk);
