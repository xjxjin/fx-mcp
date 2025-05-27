import asyncio
import os
from typing import List, Dict, Optional, Annotated
from fastmcp import FastMCP, Context
from pydantic import Field
import asyncpg
from dotenv import load_dotenv
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount

# 加载环境变量
load_dotenv()

# 创建FastMCP服务器实例
mcp = FastMCP(name="PostgreSQL查询服务")

# 数据库连接池
db_pool = None


async def get_db_pool():
    global db_pool
    if db_pool is None:
        # 从环境变量获取数据库连接信息
        db_user = os.getenv("DB_USER", "admin")
        db_password = os.getenv("DB_PASSWORD", "password")
        db_host = os.getenv("DB_HOST", "postgres")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "postgres")

        # 创建数据库连接池
        db_pool = await asyncpg.create_pool(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_name
        )
    return db_pool


@mcp.tool()
async def query_faq(
        question: Annotated[Optional[str], Field(description="问题关键词")] = None,
        ticket_type: Annotated[Optional[str], Field(description="工单类型")] = None,
        issue_module: Annotated[Optional[str], Field(description="问题分类")] = None,
        limit: Annotated[int, Field(description="返回结果数量限制", ge=1, le=100)] = 10,
        ctx: Context = None
) -> List[Dict]:
    """
    查询奇瑞星途客户问答表(cheery_exeedcars_faq)，可根据问题关键词、工单类型、问题分类进行筛选
    """
    await ctx.info(f"正在查询FAQ数据...")

    # 获取数据库连接池
    pool = await get_db_pool()

    # 构建SQL查询
    query = "SELECT * FROM public.cheery_exeedcars_faq WHERE 1=1"
    params = []
    param_index = 1

    if question:
        query += f" AND question ILIKE ${param_index}"
        params.append(f'%{question}%')
        param_index += 1

    if ticket_type:
        query += f" AND ticket_type = ${param_index}"
        params.append(ticket_type)
        param_index += 1

    if issue_module:
        query += f" AND issue_module = ${param_index}"
        params.append(issue_module)
        param_index += 1

    query += f" ORDER BY create_at DESC LIMIT ${param_index}"
    params.append(limit)

    # 执行查询
    async with pool.acquire() as conn:
        results = await conn.fetch(query, *params)

    # 转换结果为字典列表
    return [dict(row) for row in results]


@mcp.tool()
async def query_menu(
        menu_name: Annotated[Optional[str], Field(description="菜单名称关键词")] = None,
        parent_id: Annotated[Optional[int], Field(description="父级菜单ID")] = None,
        menu_type: Annotated[Optional[str], Field(description="菜单类型")] = None,
        is_disable: Annotated[Optional[str], Field(description="是否禁用，0-未禁用，1-已禁用")] = None,
        limit: Annotated[int, Field(description="返回结果数量限制", ge=1, le=100)] = 10,
        ctx: Context = None
) -> List[Dict]:
    """
    查询系统菜单表(sys_menu)，可根据菜单名称、父级ID、菜单类型和禁用状态进行筛选
    """
    await ctx.info(f"正在查询菜单数据...")

    # 获取数据库连接池
    pool = await get_db_pool()

    # 构建SQL查询
    query = "SELECT * FROM public.sys_menu WHERE 1=1"
    params = []
    param_index = 1

    if menu_name:
        query += f" AND menu_name ILIKE ${param_index}"
        params.append(f'%{menu_name}%')
        param_index += 1

    if parent_id is not None:
        query += f" AND parent_id = ${param_index}"
        params.append(parent_id)
        param_index += 1

    if menu_type:
        query += f" AND menu_type = ${param_index}"
        params.append(menu_type)
        param_index += 1

    if is_disable is not None:
        query += f" AND is_disable = ${param_index}"
        params.append(is_disable)
        param_index += 1

    query += f" ORDER BY sort ASC, create_time DESC LIMIT ${param_index}"
    params.append(limit)

    # 执行查询
    async with pool.acquire() as conn:
        results = await conn.fetch(query, *params)

    # 转换结果为字典列表
    return [dict(row) for row in results]


@mcp.tool()
async def get_faq_statistics(ctx: Context = None) -> Dict:
    """
    获取奇瑞星途客户问答表的统计信息，包括总数、各工单类型数量、各问题分类数量
    """
    await ctx.info("正在统计FAQ数据...")

    # 获取数据库连接池
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        # 获取总数
        total_count = await conn.fetchval("SELECT COUNT(*) FROM public.cheery_exeedcars_faq")

        # 获取各工单类型数量
        ticket_type_stats = await conn.fetch(
            "SELECT ticket_type, COUNT(*) as count FROM public.cheery_exeedcars_faq GROUP BY ticket_type"
        )

        # 获取各问题分类数量
        issue_module_stats = await conn.fetch(
            "SELECT issue_module, COUNT(*) as count FROM public.cheery_exeedcars_faq GROUP BY issue_module"
        )

    return {
        "total_count": total_count,
        "ticket_type_stats": [dict(row) for row in ticket_type_stats],
        "issue_module_stats": [dict(row) for row in issue_module_stats]
    }


@mcp.tool()
async def get_menu_statistics(ctx: Context = None) -> Dict:
    """
    获取系统菜单表的统计信息，包括菜单总数、各类型菜单数量、启用/禁用菜单数量
    """
    await ctx.info("正在统计菜单数据...")

    # 获取数据库连接池
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        # 获取总数
        total_count = await conn.fetchval("SELECT COUNT(*) FROM public.sys_menu")

        # 获取各菜单类型数量
        menu_type_stats = await conn.fetch(
            "SELECT menu_type, COUNT(*) as count FROM public.sys_menu GROUP BY menu_type"
        )

        # 获取启用/禁用菜单数量
        status_stats = await conn.fetch(
            "SELECT is_disable, COUNT(*) as count FROM public.sys_menu GROUP BY is_disable"
        )

    return {
        "total_count": total_count,
        "menu_type_stats": [dict(row) for row in menu_type_stats],
        "status_stats": [dict(row) for row in status_stats]
    }


# 初始化和清理函数
async def startup():
    """服务启动时初始化数据库连接池"""
    await get_db_pool()
    print("数据库连接池已初始化")


async def shutdown():
    """服务关闭时关闭数据库连接池"""
    global db_pool
    if db_pool:
        await db_pool.close()
        print("数据库连接池已关闭")
        db_pool = None


if __name__ == "__main__":
    # 从环境变量获取配置
    transport_mode = os.getenv("TRANSPORT_MODE", "http").lower()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8086"))
    
    # 初始化数据库连接
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup())
    
    try:
        if transport_mode == "stdio":
            # STDIO模式 - 适用于终端或命令行客户端
            print("正在使用STDIO模式启动PostgreSQL查询服务...")
            mcp.run(transport="stdio")
            
        elif transport_mode == "sse":
            # SSE模式 - 适用于SSE客户端
            print(f"正在使用SSE模式启动PostgreSQL查询服务，端点位于: http://{host}:{port}/mcp/sse")
            mcp.run(transport="sse", host=host, port=port)
            
        else:
            # HTTP模式 - 适用于Web客户端或Dify等平台
            print(f"正在使用HTTP模式启动PostgreSQL查询服务，端点位于: http://{host}:{port}/mcp")
            mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")
            
    except KeyboardInterrupt:
        print("服务已通过键盘中断停止")
    finally:
        # 关闭数据库连接
        loop.run_until_complete(shutdown()) 