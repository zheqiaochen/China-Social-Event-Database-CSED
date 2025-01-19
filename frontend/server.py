from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import uvicorn
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

# 加载环境变量
# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录路径（当前目录的父目录）
root_dir = os.path.dirname(current_dir)
# 加载根目录下的 .env 文件
load_dotenv(os.path.join(root_dir, '.env'))

app = FastAPI()

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB 连接
client = MongoClient(os.getenv('MONGO_URI'))
db = client['weibo']
collection = db['weibo']

# API 路由 - 注意：必须在静态文件挂载之前定义所有API路由
@app.get("/api/events")
async def get_events():
    try:
        # 修改 pipeline，添加 summary_embedding_cluster_label 的过滤条件
        pipeline = [
            {
                "$match": {
                    "event_id": {"$exists": True},
                    "event_title": {"$exists": True},
                    "text": {"$exists": True},
                    "summary_embedding_cluster_label": {"$exists": True, "$ne": -1}
                }
            },
            {
                "$sort": {"created_at": -1}
            },
            {
                "$group": {
                    "_id": "$event_id",
                    "event_title": {"$first": "$event_title"},
                    "posts": {
                        "$push": {
                            "id": "$id",
                            "text": "$text",
                            "screen_name": "$screen_name",
                            "attitudes_count": "$attitudes_count",
                            "comments_count": "$comments_count",
                            "reposts_count": "$reposts_count",
                            "created_at": "$created_at",
                            "response": {"$ifNull": ["$response", 0]}
                        }
                    }
                }
            }
        ]
        
        documents = list(collection.aggregate(pipeline))
        
        if not documents:
            print("没有找到任何事件数据")
            return {"events": []}
            
        print(f"成功获取到 {len(documents)} 个事件")
        return {"events": documents}
        
    except Exception as e:
        print(f"获取事件数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test")
async def test_connection():
    try:
        # 测试数据库连接
        count = collection.count_documents({})
        return {
            "status": "success",
            "message": f"MongoDB连接成功，共有 {count} 条数据"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"MongoDB连接失败: {str(e)}"
        )

@app.get("/api/valid_clusters")
async def get_valid_clusters():
    try:
        # 查询条件：排除 summary_embedding_cluster_label 为 -1 的文档
        pipeline = [
            {
                "$match": {
                    "summary_embedding_cluster_label": {"$exists": True, "$ne": -1},
                    "event_id": {"$exists": True},
                    "event_title": {"$exists": True}
                }
            },
            {
                "$sort": {"created_at": -1}  # 按时间倒序排序
            },
            {
                "$group": {
                    "_id": "$event_id",
                    "event_title": {"$first": "$event_title"},
                    "cluster_label": {"$first": "$summary_embedding_cluster_label"},
                    "posts": {
                        "$push": {
                            "text": "$text",
                            "summary": "$summary",
                            "created_at": "$created_at"
                        }
                    }
                }
            }
        ]
        
        documents = list(collection.aggregate(pipeline))
        
        if not documents:
            print("没有找到任何有效聚类数据")
            return {"clusters": []}
            
        print(f"成功获取到 {len(documents)} 个有效聚类")
        return {"clusters": documents}
        
    except Exception as e:
        print(f"获取聚类数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 静态文件挂载
app.mount("/", StaticFiles(directory="dist", html=True, check_dir=False), name="static")

# 添加一个回退路由处理程序
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return FileResponse("dist/index.html")

if __name__ == "__main__":
    import uvicorn
    print("启动服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 