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

@app.get("/api/events")
async def get_events():
    """
    获取事件列表
    """
    try:
        pipeline = [
            {
                "$match": {
                    "event_title": {"$exists": True},
                    "text": {"$exists": True},
                    "summary_embedding_cluster_label": {"$exists": True, "$ne": -1}
                }
            },
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$summary_embedding_cluster_label",
                    "event_title": {"$first": "$event_title"},
                    "latest_post": {
                        "$first": {
                            "created_at": "$created_at"
                        }
                    },
                    "earliest_post": {
                        "$last": {
                            "created_at": "$created_at"
                        }
                    },
                    "posts_count": {"$sum": 1}
                }
            }
        ]
        
        # 关键修正：使用 allowDiskUse=True 时，需在 aggregate() 方法里直接指定，而不是对 list(...) 再调用
        documents = list(collection.aggregate(pipeline, allowDiskUse=True))
        
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
    """
    测试数据库连接
    """
    try:
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
    """
    获取有效的聚类信息，基于 summary_embedding_cluster_label。
    """
    try:
        pipeline = [
            {
                "$match": {
                    "summary_embedding_cluster_label": {"$exists": True, "$ne": -1},
                    "event_title": {"$exists": True}
                }
            },
            {
                "$sort": {"created_at": -1}
            },
            {
                "$group": {
                    "_id": "$summary_embedding_cluster_label",
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
        
        # 关键修正：不要对 list(...) 之后再调用 .allowDiskUse(True)
        documents = list(collection.aggregate(pipeline, allowDiskUse=True))
        
        if not documents:
            print("没有找到任何有效聚类数据")
            return {"clusters": []}
            
        print(f"成功获取到 {len(documents)} 个有效聚类（基于 summary_embedding_cluster_label）")
        return {"clusters": documents}
        
    except Exception as e:
        print(f"获取聚类数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/event_posts/{event_id}")
async def get_event_posts(event_id: int):
    """
    根据 summary_embedding_cluster_label（event_id）获取对应帖子
    """
    try:
        print(f"正在获取事件ID: {event_id} 的帖子")
        
        pipeline = [
            {
                "$match": {
                    "summary_embedding_cluster_label": event_id
                }
            },
            {"$sort": {"created_at": -1}},
            {
                "$project": {
                    "id": 1,
                    "text": 1,
                    "screen_name": 1,
                    "attitudes_count": 1,
                    "comments_count": 1,
                    "reposts_count": 1,
                    "created_at": 1,
                    "response": {"$ifNull": ["$response", 0]}
                }
            }
        ]
        
        try:
            posts = list(collection.aggregate(pipeline, allowDiskUse=True))
            print(f"成功获取到 {len(posts)} 条帖子")
            
            # 使用 json_util 处理 MongoDB 的特殊类型
            json_str = json_util.dumps({"posts": posts})
            json_data = json.loads(json_str)
            
            return JSONResponse(content=json_data)
            
        except Exception as db_error:
            print(f"数据库查询失败: {str(db_error)}")
            raise db_error
            
    except Exception as e:
        print(f"获取帖子失败: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"获取帖子失败: {str(e)}, 事件ID: {event_id}"
        )

# 静态文件挂载；确保 dist 目录中存在 index.html 和相关静态文件
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # 获取上一级目录
dist_path = os.path.join(parent_dir, "dist")  # 指向上一级的 dist 目录

app.mount("/", StaticFiles(directory=dist_path, html=True, check_dir=False), name="static")

# 回退路由处理，将 404 请求重定向到前端 index.html (SPA 场景)
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return FileResponse("dist/index.html")

if __name__ == "__main__":
    print("启动服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
