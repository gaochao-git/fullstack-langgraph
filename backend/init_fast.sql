create table agent_configs like omind.agent_configs;
create table agent_document_session like omind.agent_document_session;
create table agent_document_upload like omind.agent_document_upload;
create table ai_model_configs like omind.ai_model_configs;
create table auth_api_keys like omind.auth_api_keys;
create table auth_login_history like omind.auth_login_history;
create table auth_sessions like omind.auth_sessions;
create table auth_tokens like omind.auth_tokens;
create table celery_periodic_task_configs like omind.celery_periodic_task_configs;
create table celery_periodic_task_execution_logs like omind.celery_periodic_task_execution_logs;
create table celery_task_records like omind.celery_task_records;
create table celery_taskmeta like omind.celery_taskmeta;
create table celery_tasksetmeta like omind.celery_tasksetmeta;
create table mcp_configs like omind.mcp_configs;
create table mcp_servers like omind.mcp_servers;
create table rbac_menus like omind.rbac_menus;
create table rbac_permissions like omind.rbac_permissions;
create table rbac_roles like omind.rbac_roles;
create table rbac_roles_permissions like omind.rbac_roles_permissions;
create table rbac_users like omind.rbac_users;
create table rbac_users_roles like omind.rbac_users_roles;
create table sop_problem_rule like omind.sop_problem_rule;
create table sop_prompt_templates like omind.sop_prompt_templates;
create table user_threads like omind.user_threads;
create table agent_permission like omind.agent_permission;
create table kb_categories like omind.kb_categories;
create table kb_document_folders like omind.kb_document_folders;
create table kb_documents like omind.kb_documents;
create table kb_folders like omind.kb_folders;
create table kb_permissions like omind.kb_permissions;
create table knowledge_bases like omind.knowledge_bases;

insert into rbac_users select * from omind.rbac_users;
insert into rbac_roles select * from omind.rbac_roles;
insert into rbac_menus select * from omind.rbac_menus;
insert into rbac_permissions select * from omind.rbac_permissions;
insert into rbac_users_roles select * from omind.rbac_users_roles;
insert into rbac_roles_permissions select * from omind.rbac_roles_permissions;
insert into agent_configs select * from omind.agent_configs;

# 备份语句
/home/mysql/multi/3306/mysql57/bin/mysqldump -h127.0.0.1 -uroot -pfffjjj --set-gtid-purged=OFF --single-transaction --master-data=2 --skip-tz-utc --default-character-set=utf8mb4 -d omind_prd >omind_prd_frm.sql
/home/mysql/multi/3306/mysql57/bin/mysqldump -h127.0.0.1 -uroot -pfffjjj --set-gtid-purged=OFF --single-transaction --master-data=2 --skip-tz-utc --default-character-set=utf8mb4 omind_prd rbac_users rbac_roles rbac_menus rbac_permissions rbac_users_roles rbac_roles_permissions agent_configs >omind_prd_data.sql
