# CAS Server 快速启动指南

## 一键启动

```bash
cd cas-server
./start-cas.sh
```

或者直接使用 Docker Compose：

```bash
cd cas-server
docker-compose up -d
```

## 默认配置

- **访问地址**: http://localhost:8080/cas
- **测试用户**:
  - casuser / Mellon
  - admin / admin123
  - zhangsan / 123456

## 与 OMind 集成

在 OMind 后端配置中设置：

```python
# .env 文件
CAS_SERVER_URL=http://localhost:8080/cas
CAS_SERVICE_URL=http://localhost:3000/api/v1/auth/sso/callback
CAS_VERSION=3
```

## 自定义用户

修改 `docker-compose.yml` 中的 `CAS_AUTHN_ACCEPT_USERS` 环境变量：

```yaml
CAS_AUTHN_ACCEPT_USERS=user1::pass1,user2::pass2
```

## 模拟 LDAP 属性

创建 `config/cas.properties` 文件来配置用户属性：

```properties
cas.authn.attribute-repository.stub.attributes.zhangsan.display_name=张三
cas.authn.attribute-repository.stub.attributes.zhangsan.email=zhangsan@taobao.com
cas.authn.attribute-repository.stub.attributes.zhangsan.group_name=CN=张三,OU=开发组,OU=技术部,OU=淘宝,DC=taobao,DC=COM
```

## 停止服务

```bash
docker-compose down
```