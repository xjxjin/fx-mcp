# FastMCP PostgreSQL查询服务

这是一个使用FastMCP构建的PostgreSQL数据库查询服务，支持查询两个表：奇瑞星途客户问答(`cheery_exeedcars_faq`)和系统菜单(`sys_menu`)。

## 功能特点

- 支持通过问题关键词、工单类型、问题分类查询FAQ数据
- 支持通过菜单名称、父级ID、菜单类型、禁用状态查询菜单数据
- 提供FAQ和菜单的统计信息查询功能
- 基于Docker容器化部署，包含PostgreSQL数据库和FastMCP应用
- 自动初始化数据库表结构和示例数据
- 支持多种MCP连接方式：STDIO、Streamable HTTP和SSE

## 快速开始


### 前提条件

- 安装Docker和Docker Compose
- 确保端口5432和8080未被占用

### 部署步骤

1. 克隆本仓库

```bash
git clone <仓库地址>
cd <项目目录>
```

2. 启动服务

```bash
docker-compose up -d
```

3. 验证服务

FastMCP服务将在8080端口运行，PostgreSQL数据库在5432端口运行。您可以通过以下URL访问MCP服务：

- HTTP端点：`http://localhost:8080/mcp`
- SSE端点：`http://localhost:8080/mcp/sse`

### 配置说明

可以通过修改`.env`文件或`docker-compose.yml`文件中的环境变量来自定义配置：

- 数据库配置：
  - `DB_USER`: 数据库用户名
  - `DB_PASSWORD`: 数据库密码
  - `DB_HOST`: 数据库主机名
  - `DB_PORT`: 数据库端口
  - `DB_NAME`: 数据库名称

- 服务器配置：
  - `TRANSPORT_MODE`: 传输模式，可选值为`stdio`或`http`(默认)
  - `HOST`: 服务器主机名，默认为`0.0.0.0`
  - `PORT`: 服务器端口，默认为`8080`

## 可用工具

FastMCP服务提供以下工具：

1. `query_faq` - 查询奇瑞星途客户问答数据
2. `query_menu` - 查询系统菜单数据
3. `get_faq_statistics` - 获取FAQ数据统计信息
4. `get_menu_statistics` - 获取菜单数据统计信息

## 数据库表结构

### cheery_exeedcars_faq (奇瑞星途客户问答)

| 列名 | 类型 | 描述 |
|------|------|------|
| id | int4 | 主键ID |
| question | text | 问题 |
| answer | text | 答案 |
| ticket_type | varchar(255) | 工单类型 |
| issue_module | varchar(255) | 问题分类 |
| create_at | timestamp(6) | 创建时间 |

### sys_menu (系统菜单表)

| 列名 | 类型 | 描述 |
|------|------|------|
| menu_id | int8 | 菜单ID (主键) |
| parent_id | int8 | 父级菜单ID，无父级为0 |
| menu_name | varchar(100) | 菜单名称 |
| menu_icon | varchar(255) | 菜单icon |
| menu_url | varchar(255) | 菜单路由 |
| menu_type | varchar(255) | 类型0-应用1-菜单2-按钮 |
| is_outside | char(1) | 是否外链0-内链1-外链 |
| is_disable | char(1) | 是否禁用0-未禁用1-已禁用 |
| create_time | timestamp(6) | 创建时间 |
| create_user | int8 | 创建人 |
| last_edit_time | timestamp(6) | 最后一次修改时间 |
| last_edit_user | int8 | 最后一次修改人 |
| sort | int2 | 排序 |

## 使用示例

### 客户端连接方式

根据不同的客户端需求，有以下几种连接方式：

#### 1. Python客户端

```python
from fastmcp import Client

async def main():
    # STDIO连接（命令行工具）
    async with Client("./app.py") as client:
        result = await client.call_tool("query_faq", {"question": "轮胎"})
    
    # HTTP连接（Web服务）
    async with Client("http://localhost:8080/mcp") as client:
        result = await client.call_tool("query_menu", {"parent_id": 1})
    
    # SSE连接（Web服务）
    async with Client("http://localhost:8080/mcp/sse") as client:
        result = await client.call_tool("get_faq_statistics")
```

#### 2. Dify集成

在Dify中，配置MCP工具连接时，可以使用以下URL：
- HTTP模式：`http://服务器IP:8080/mcp`
- SSE模式：`http://服务器IP:8080/mcp/sse`

### 工具调用示例

#### 查询FAQ数据

```python
# 查询包含"轮胎"关键词的FAQ
result = await client.call_tool("query_faq", {"question": "轮胎"})

# 查询工单类型为"技术支持"的FAQ
result = await client.call_tool("query_faq", {"ticket_type": "技术支持"})

# 查询问题分类为"智能系统"的FAQ，限制返回5条
result = await client.call_tool("query_faq", {"issue_module": "智能系统", "limit": 5})
```

#### 查询菜单数据

```python
# 查询父级ID为1的菜单
result = await client.call_tool("query_menu", {"parent_id": 1})

# 查询菜单名称包含"管理"的菜单
result = await client.call_tool("query_menu", {"menu_name": "管理"})

# 查询菜单类型为"1"且未禁用的菜单
result = await client.call_tool("query_menu", {"menu_type": "1", "is_disable": "0"})
```

#### 获取统计信息

```python
# 获取FAQ统计信息
faq_stats = await client.call_tool("get_faq_statistics")

# 获取菜单统计信息
menu_stats = await client.call_tool("get_menu_statistics")
``` 