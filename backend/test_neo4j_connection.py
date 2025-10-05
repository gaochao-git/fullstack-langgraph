"""
测试Neo4j连接
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_neo4j_connection():
    """测试Neo4j连接"""
    try:
        from neo4j import GraphDatabase

        # 读取配置
        url = os.getenv("NEO4J_URL", "bolt://82.156.146.51:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "Neo4jPassword123")

        print(f"🔗 连接Neo4j: {url}")
        print(f"   用户名: {username}")

        # 创建驱动
        driver = GraphDatabase.driver(url, auth=(username, password))

        # 验证连接
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            record = result.single()
            print(f"✅ Neo4j连接成功! 测试查询返回: {record['test']}")

            # 获取版本信息
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            for record in result:
                print(f"   Neo4j版本: {record['name']} {record['versions'][0]} ({record['edition']})")

        driver.close()
        return True

    except Exception as e:
        print(f"❌ Neo4j连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_neo4j_connection()
    sys.exit(0 if success else 1)
