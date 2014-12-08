CREATE INDEX
   store_index
ON
   store_sales (ss_store_sk) include (ss_net_paid, ss_net_profit);
