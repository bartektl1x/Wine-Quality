source:
  catalog: bronze_catalog
  schema: system1_raw

target:
  catalog: bronze_catalog
  schema: system1_raw_standardized

tables:
  - source_table: table1
  - source_table: table2





source:
  catalog: business_catalog
  schema: gold

target:
  catalog: business_catalog
  schema: gold

tables:
  - source_table: table1
    target_table: table1_checked

  - source_table: table2
    target_table: table2_checked
