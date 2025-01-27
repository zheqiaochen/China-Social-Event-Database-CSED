import logging
import numpy as np
import hdbscan
import sys
import datetime
import os
import numpy as np
from dotenv import load_dotenv
from tqdm import tqdm
from pymongo import MongoClient
from openai import OpenAI

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录路径（当前目录的父目录）
root_dir = os.path.dirname(current_dir)
# 加载根目录下的 .env 文件
load_dotenv(os.path.join(root_dir, '.env'))

logger = logging.getLogger(__name__)
 
class InfoProcessor:
    """
    从数据库取数据、调用OpenAI API获得结果，然后写回数据库
    包括预处理（process_text）、摘要（summary）、聚类（do_hdbscan）、生成事件标题（generate_cluster_titles）
    """
    def __init__(self, config: dict):
        """
        初始化处理器
        Args:
            config: 配置字典，包含以下参数:
                - MONGO_URI: MongoDB数据库连接URI
                - API_KEY: OpenAI API密钥
                - CHAT_MODEL: 使用的GPT聊天模型名称
                - EMBED_MODEL: 使用的文本嵌入模型名称
                - TEMPERATURE: GPT生成结果的随机性参数(0-1)
                - MIN_CLUSTER_SIZE: HDBSCAN聚类的最小簇大小
                - MIN_SAMPLES: HDBSCAN聚类的最小样本数
                - EPSILON: HDBSCAN聚类的邻域大小参数
                - DELETE_OLD_DAYS: 删除多少天前的旧数据
                - ARCHIVE_OLD_DAYS: 归档多少天前的旧数据
        """
        # 初始化数据库连接
        try:
            self.mongo_client = MongoClient(os.getenv('MONGO_URI'))
            self.db = self.mongo_client['weibo']
            self.collection = self.db['weibo']
            logger.info('MongoDB连接成功')
        except Exception as e:
            logger.error(f'MongoDB连接失败: {e}')
            raise e

        # 初始化OpenAI客户端
        self.client = OpenAI(api_key=os.getenv('API_KEY'))
        self.chat_model = config['CHAT_MODEL']
        self.embed_model = config['EMBED_MODEL']
        self.temperature = config['TEMPERATURE']

        # 聚类配置
        self.cluster_config = {
            'min_cluster_size': config['MIN_CLUSTER_SIZE'],
            'min_samples': config['MIN_SAMPLES'],
            # 可以设置epsilon，这里先注释掉了，如果需要取消注释
            # 'epsilon': config['EPSILON']
        }
        self.delete_old_days = config['DELETE_OLD_DAYS']
        self.archive_old_days = config['ARCHIVE_OLD_DAYS']


    def generate_summary_response(self, user_prompt: str) -> str:
        """生成摘要和回应信息"""
        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"调用 GPT Chat 出错: {e}")
            return ""


    def generate_embedding(self, input_text: str) -> list:
        """生成文本的embedding向量"""
        try:
            response = self.client.embeddings.create(
                input=input_text,
                model=self.embed_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"调用 Embedding 出错: {e}")
            return []

    def delete_old(self):
        """
        删除指定天数前的、且聚类结果为 -1（噪声点）的数据
        """
        days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=self.delete_old_days)).isoformat()

        query = {
            "created_at": {"$lt": days_ago},
            "summary_embedding_cluster_label": -1
        }

        result = self.collection.delete_many(query)
        logger.info(f"已删除 {result.deleted_count} 条符合条件的数据。")

    def process_text(self, text: str) -> str:
        """
        轻量级清洗或预处理
        """
        return text.strip()


    def summary(self) -> None:
        """
        为所有文档生成15个字以内的摘要，判断是否包含政府回应以及机构。
        """
        documents = list(self.collection.find(
            {"summary": {"$exists": False}, "response": {"$exists": False}, "org": {"$exists": False}, "archived": {"$ne": 1}}, 
            {"_id": 1, "text": 1}
        ))
        updated_count = 0

        for doc in tqdm(documents, desc="正在生成文档摘要和政府回应", file=sys.stdout):
            doc_text = doc.get("text", "")
            if not doc_text:
                continue

            prompt = (
                f"根据这段文本，输出15个字以内的摘要，包含你认为最关键的信息。"
                f"并且判断这段文本里是否包含中国国家机构对这一新闻事件的回应，如果包含的话返回1，不包含的话返回0。"
                f"如果包含中国国家机构回应，则返回国家机构名称（如果找不到，则返回空字符串）。\n\n"
                f"请按照以下格式返回：\n"
                f"摘要：[摘要内容]\n"
                f"回应：[0或1]\n"
                f"机构：[机构名称]\n\n"
                f"{doc_text}"
            )
            
            summary_text = self.generate_summary_response(prompt)
            if summary_text:
                # 解析返回的文本
                try:
                    lines = summary_text.split('\n')
                    summary_content = lines[0].split('：')[1].strip() if len(lines) > 0 else ""
                    response_value = int(lines[1].split('：')[1].strip()) if len(lines) > 1 else 0
                    org_name = lines[2].split('：')[1].strip() if len(lines) > 2 else ""
                except Exception as e:
                    logger.error(f"解析返回结果失败: {e}, 原始返回: {summary_text}")
                    continue

                try:
                    self.collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {
                            "summary": summary_content,
                            "response": response_value,
                            "org": org_name
                        }}
                    )
                    updated_count += 1
                except Exception as e:
                    logger.error(f"数据库更新失败: {e}, 文档ID: {doc['_id']}")
                    continue

        logger.info(f"共处理并更新了 {updated_count} 篇文档的摘要和政府回应。")


    def summary_embedding(self):
        """
        对 summary 字段做Embedding
        """
        documents = list(self.collection.find(
            {"summary_embedding": {"$exists": False}, "archived": {"$ne": 1}}, 
            {"_id": 1, "summary": 1}
        ))

        processed_count = 0
        for doc in tqdm(documents, desc="正在生成embedding", file=sys.stdout):
            raw_text = doc.get("summary", "")
            if not raw_text:
                continue

            processed_text = self.process_text(raw_text)
            embedding = self.generate_embedding(processed_text)
            if embedding:
                self.collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"summary_embedding": embedding}}
                )
                processed_count += 1

        logger.info(f"新处理了 {processed_count} 个文档的摘要GPT句向量！")


    def do_hdbscan(self):
        """
        使用HDBSCAN进行聚类，并更新文档的 summary_embedding_cluster_label 字段
        """
        documents = list(self.collection.find({
            "summary_embedding": {"$exists": True}
            "archived": {"$ne": 1}
        }))
        if not documents:
            logger.warning("没有任何文档包含 summary_embedding，无法聚类。")
            return

        X = np.array([doc["summary_embedding"] for doc in documents], dtype=np.float32)
        logger.info(f"正在对字段 'summary_embedding' 做 HDBSCAN 聚类: X shape = {X.shape}")

        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.cluster_config['min_cluster_size'],
            min_samples=self.cluster_config['min_samples'],
            # 可以设置epsilon，这里先注释掉了，如果需要取消注释
            # cluster_selection_epsilon=self.cluster_config['epsilon'],
        )
        cluster_labels = self.clusterer.fit_predict(X)
        
        for doc, label in zip(documents, cluster_labels):
            self.collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"summary_embedding_cluster_label": int(label)}}
            )

        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        logger.info(f"字段 'summary_embedding' 聚类完成，共识别出 {n_clusters} 个簇。")


    def generate_cluster_titles(self):
        """
        为满足最小簇大小要求的簇生成标题。
        使用 summary_embedding_cluster_label 作为唯一标识，不再生成 event_id。
        """
        # 确保我已经做过 do_hdbscan
        clusterer = getattr(self, 'clusterer', None)
        if not clusterer:
            logger.warning("尚未进行 HDBSCAN 聚类，无法生成事件标题。请先调用 do_hdbscan()。")
            return

        # 一次性拿到所有尚未设置 event_title 的文档
        docs = list(self.collection.find({
            "summary_embedding_cluster_label": {"$exists": True},
            "event_title": {"$exists": False},
            "archived": {"$ne": 1}
        }))

        # 按簇号进行分组, 排除噪声点(-1)
        cluster_map = {}
        for doc in docs:
            cluster_label = doc.get("summary_embedding_cluster_label")
            if cluster_label is not None and cluster_label != -1:
                cluster_map.setdefault(cluster_label, []).append(doc)

        # 逐个处理簇
        for cluster_label, cluster_docs in cluster_map.items():
            # 检查簇的大小是否满足最小要求
            if len(cluster_docs) < self.cluster_config['min_cluster_size']:
                continue

            # 找到这个簇在HDBSCAN计算中的“中心点”Embedding
            centroid_vector = hdbscan.HDBSCAN.weighted_cluster_medoid(
                self=clusterer, 
                cluster_id=cluster_label
            ).tolist()

            # 在数据库中找到该中心点对应的文档
            result = self.collection.find_one(
                {"summary_embedding": {"$eq": centroid_vector}}
            )
            if not result:
                logger.warning(f"簇 {cluster_label} 的簇中心文档没有找到，跳过。")
                continue

            doc_text = result.get('text', "")
            if not doc_text:
                logger.warning(f"簇 {cluster_label} 的中心文档没有 text，跳过。")
                continue
            
            # 生成标题的prompt
            prompt = (
                "为这段新闻拟一个能简要概括事件的标题\n"
                "（仅输出标题文本，不超过15个汉字）：\n\n"
                f"{doc_text}"
            )

            # 调用 GPT 生成标题
            title = self.generate_summary_response(prompt)
            if not title:
                logger.warning(f"GPT 未返回标题，跳过簇 {cluster_label}。")
                continue

            # 为该簇所有文档写入同一个标题
            update_result = self.collection.update_many(
                {"summary_embedding_cluster_label": cluster_label},
                {"$set": {
                    "event_title": title
                }}
            )
            logger.info(
                f"为簇号 {cluster_label} 生成标题：{title}，"
                f"并更新了 {update_result.modified_count} 篇文档。"
            )


    def archive_inactive_events(self):
        """
        将“长时间没有更新”的事件归档：
        1. 聚合获取每个 event_title 的“最新”一条微博时间
        2. 若最后一条微博时间早于设定天数(archive_old_days)前，则将该事件标记为 archived=1
        3. 同时将该事件的 summary_embedding_cluster_label 改为一个随机值（>999999），避免再被视为活跃事件
        """
        # 1) 聚合获取每个 event_title 的最新微博时间
        last_events = list(self.collection.aggregate([
            {"$match": {"event_title": {"$exists": True}, "archived": {"$ne": 1}}},
            {"$sort": {"event_title": 1, "created_at": -1}},  # 同一事件下按时间逆序
            {"$group": {
                "_id": "$event_title",
                "last_weibo": {"$first": "$created_at"}
            }},
        ]))

        # 2) 生成与事件数量等长的、无重复的随机整数，且都大于 999999
        event_count = len(last_events)
        unique_labels = np.random.choice(
            np.arange(1_000_000, 10_000_000),
            size=event_count,
            replace=False
        )

        # 3) 对比时间，超过 threshold 即归档
        now = datetime.datetime.utcnow()
        threshold_time = now - datetime.timedelta(days=self.archive_old_days)

        archived_count = 0
        for i, last_event in enumerate(last_events):
            last_weibo_time = last_event.get("last_weibo")
            event_title = last_event.get("_id")

            # 注意：数据库中的 created_at 若是字符串，需要转为 datetime 对象比较
            if isinstance(last_weibo_time, str):
                try:
                    last_weibo_time = datetime.datetime.fromisoformat(last_weibo_time)
                except ValueError:
                    logger.warning(f"无法将 {last_weibo_time} 转为 datetime，跳过归档判断。")
                    continue

            if last_weibo_time < threshold_time:
                # 更新该 event_title 的所有文档
                new_label = int(unique_labels[i])
                self.collection.update_many(
                    {"event_title": event_title},
                    {
                        "$set": {
                            "archived": 1,
                            "summary_embedding_cluster_label": new_label
                        }
                    }
                )
                archived_count += 1
                logger.info(f"已归档事件: {event_title}, 最后一条微博时间: {last_weibo_time}, 新的 cluster_label = {new_label}")

        logger.info(f"检查了 {event_count} 个事件，共归档了 {archived_count} 个事件。")
