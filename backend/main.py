import logging
import uvicorn
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from info_processor import InfoProcessor


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('log/app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 配置管理
config_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + "config.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 创建服务实例
info_processor = InfoProcessor(config)

class ProcessResponse(BaseModel):
    status: str
    message: str

# 创建FastAPI
app = FastAPI(title="事件信息系统API",
             description="事件信息处理和分析",
             version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "新闻信息系统API服务正在运行"}

@app.post("/api/process/delete_old")
async def delete_old():
    try:
        info_processor.delete_old()
        return ProcessResponse(status="success", message="旧数据删除完成")
    except Exception as e:
        logger.error(f"旧数据删除错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process/summary")
async def process_summary():
    try:
        info_processor.summary()
        return ProcessResponse(status="success", message="摘要生成完成")
    except Exception as e:
        logger.error(f"摘要生成错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process/embedding")
async def process_embedding():
    try:
        info_processor.summary_embedding()
        return ProcessResponse(status="success", message="摘要级别GPT Embedding完成")
    except Exception as e:
        logger.error(f"Embedding处理错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cluster/hdbscan")
async def cluster_hdbscan():
    try:
        info_processor.do_hdbscan()
        return ProcessResponse(status="success", message="HDBSCAN聚类完成")
    except Exception as e:
        logger.error(f"HDBSCAN聚类错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/cluster/fishdbc")
# async def cluster_fishdbc():
#     try:
#         info_processor.do_fishdbc()
#         return ProcessResponse(status="success", message="FISHDBC聚类完成")
#     except Exception as e:
#         logger.error(f"FISHDBC聚类错误: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cluster/titles")
async def generate_titles():
    try:
        info_processor.generate_cluster_titles()
        return ProcessResponse(status="success", message="聚类标题生成完成")
    except Exception as e:
        logger.error(f"标题生成错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process/archive_inactive_events")
async def archive_inactive_events():
    try:
        info_processor.archive_inactive_events()
        return ProcessResponse(status="success", message="已归档事件完成")
    except Exception as e:
        logger.error(f"已归档事件错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)