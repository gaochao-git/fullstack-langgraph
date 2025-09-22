# 备份语句
/home/mysql/multi/3306/mysql57/bin/mysqldump -h127.0.0.1 -uroot -pfffjjj --set-gtid-purged=OFF --single-transaction --master-data=2 --skip-tz-utc --default-character-set=utf8mb4 -d omind >omind_prd_frm.sql
/home/mysql/multi/3306/mysql57/bin/mysqldump -h127.0.0.1 -uroot -pfffjjj --set-gtid-purged=OFF --single-transaction --master-data=2 --skip-tz-utc --default-character-set=utf8mb4 omind_prd rbac_roles rbac_menus rbac_permissions >omind_prd_data.sql
