import os
import logging
from typing import List,Optional, Annotated
from fastmcp import FastMCP, Context
from pydantic import Field
from dotenv import load_dotenv
import threading
import psycopg
from psycopg import Connection

from psycopg.rows import dict_row
from psycopg.rows import tuple_row
import yaml
import uuid
from collections.abc import Callable
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger("postgres-query-service")

# 加载环境变量
load_dotenv()
logger.info("环境变量已加载")

# 创建FastMCP服务器实例
mcp = FastMCP(name="PostgreSQL查询服务")

# 数据库连接池
db_pool = None
# 同步锁，用于保护数据库连接池
db_lock = threading.Lock()


def get_db_connection(row_factory: Callable[[Any], Any] = tuple_row) -> Connection:
    """
    Get a database connection

    Args:
        row_factory: The row factory to use.

    Returns:
        A database connection.
    """
    # config = get_config()
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        dbname=os.getenv("DB_NAME", "postgres"),
        row_factory=row_factory,
    )




@mcp.tool()
async def query_faq(
        question: Annotated[Optional[str], Field(description="问题关键词")] = None,
        ticket_type: Annotated[Optional[str], Field(description="工单类型")] = None,
        issue_module: Annotated[Optional[str], Field(description="问题分类")] = None,
        limit: Annotated[int, Field(description="返回结果数量限制", ge=1, le=100)] = 10,
        ctx: Context = None
) -> List[dict]:
    """
    查询奇瑞星途客户问答表(cheery_exeedcars_faq)，可根据问题关键词、工单类型、问题分类进行筛选
    """
    await ctx.info(f"正在查询FAQ数据...")
    logger.info(f"开始FAQ查询，参数: 问题={question}, 工单类型={ticket_type}, 问题分类={issue_module}, 限制={limit}")

    # 构建SQL查询
    query = "SELECT question,answer FROM public.cheery_exeedcars_faq WHERE 1=1"
    params = []

    if question:
        query += " AND question ILIKE %s"
        params.append(f'%{question}%')

    if ticket_type:
        query += " AND ticket_type = %s"
        params.append(ticket_type)

    if issue_module:
        query += " AND issue_module = %s"
        params.append(issue_module)

    query += " ORDER BY create_at DESC LIMIT %s"
    params.append(limit)

    # 记录最终SQL和参数

    debug_sql = query
    for i, param in enumerate(params):
        placeholder = "%s"
        debug_sql = debug_sql.replace(placeholder, f"'{param}'" if isinstance(param, str) else str(param), 1)

    logger.info(f"构建的SQL查询: {debug_sql}")
    logger.info(f"查询参数: {params}")
    with get_db_connection(row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(debug_sql)  # type: ignore
            rows: list[dict[str, Any]] = cursor.fetchall()  # type: ignore
    processed_rows = []
    for row in rows:
        processed_row = {}
        for key, value in row.items():
            # Convert UUID objects to strings
            if isinstance(value, uuid.UUID):
                processed_row[key] = str(value)
            else:
                processed_row[key] = value
        processed_rows.append(processed_row)

    return processed_rows



@mcp.tool()
async def query_menu(
        menu_name: Annotated[Optional[str], Field(description="菜单名称关键词")] = None,
        parent_id: Annotated[Optional[int], Field(description="父级菜单ID")] = None,
        menu_type: Annotated[Optional[str], Field(description="菜单类型")] = None,
        is_disable: Annotated[Optional[str], Field(description="是否禁用，0-未禁用，1-已禁用")] = None,
        limit: Annotated[int, Field(description="返回结果数量限制", ge=1, le=100)] = 10,
        ctx: Context = None
) -> List[dict]:
    """
    查询系统菜单表(sys_menu)，可根据菜单名称、父级ID、菜单类型和禁用状态进行筛选
    """
    await ctx.info(f"正在查询菜单数据...")
    logger.info(f"开始菜单查询，参数: 菜单名称={menu_name}, 父级ID={parent_id}, 菜单类型={menu_type}, 禁用状态={is_disable}, 限制={limit}")

    # 构建SQL查询
    query = "SELECT * FROM public.sys_menu WHERE 1=1"
    params = []

    if menu_name:
        query += " AND menu_name ILIKE %s"
        params.append(f'%{menu_name}%')

    if parent_id is not None:
        query += " AND parent_id = %s"
        params.append(parent_id)

    if menu_type:
        query += " AND menu_type = %s"
        params.append(menu_type)

    if is_disable is not None:
        query += " AND is_disable = %s"
        params.append(is_disable)

    query += " ORDER BY sort ASC, create_time DESC LIMIT %s"
    params.append(limit)

    # 记录最终SQL和参数
    debug_sql = query
    for i, param in enumerate(params):
        placeholder = "%s"
        debug_sql = debug_sql.replace(placeholder, f"'{param}'" if isinstance(param, str) else str(param), 1)

    logger.info(f"构建的SQL查询: {debug_sql}")
    logger.info(f"查询参数: {params}")

    with get_db_connection(row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(debug_sql)  # type: ignore
            rows: list[dict[str, Any]] = cursor.fetchall()  # type: ignore
    processed_rows = []
    for row in rows:
        processed_row = {}
        for key, value in row.items():
            # Convert UUID objects to strings
            if isinstance(value, uuid.UUID):
                processed_row[key] = str(value)
            else:
                processed_row[key] = value
        processed_rows.append(processed_row)

    return processed_rows



if __name__ == "__main__":
    # 从环境变量获取配置
    transport_mode = os.getenv("TRANSPORT_MODE", "http").lower()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8086"))
    
    logger.info(f"服务配置: 传输模式={transport_mode}, 主机={host}, 端口={port}")
    

    # transport_mode = "sse"
    
    try:
        if transport_mode == "stdio":
            # STDIO模式 - 适用于终端或命令行客户端
            logger.info("正在使用STDIO模式启动PostgreSQL查询服务...")
            mcp.run(transport="stdio")
            
        elif transport_mode == "sse":
            # SSE模式 - 适用于SSE客户端
            logger.info(f"正在使用SSE模式启动PostgreSQL查询服务，端点位于: http://{host}:{port}/mcp/sse")
            mcp.run(transport="sse", host=host, port=port)
            
        else:
            # HTTP模式 - 适用于Web客户端或Dify等平台
            logger.info(f"正在使用HTTP模式启动PostgreSQL查询服务，端点位于: http://{host}:{port}/mcp")
            mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")
            
    except KeyboardInterrupt:
        logger.info("服务已通过键盘中断停止")
