import hashlib
import json
import math
import re
from pathlib import Path
from typing import Dict, List

import faiss
import numpy as np
import PyPDF2
from docx import Document as DocxDocument
from openai import AsyncOpenAI

from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.index_dir = Path("indexes")
        self.index_dir.mkdir(exist_ok=True)
        self.dimension = 1024
        self.current_index = None
        self.current_documents = {}
        self.model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.model = None
        self.use_local_fallback = False
        self.embedding_client = AsyncOpenAI(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
        )

    def _create_index(self, dimension: int) -> faiss.IndexFlatL2:
        return faiss.IndexFlatL2(dimension)

    def _hash_embed_with_dimension(self, text: str, dimension: int) -> np.ndarray:
        vector = np.zeros(dimension, dtype="float32")
        tokens = self._tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            bucket = hash(token) % dimension
            vector[bucket] += 1.0

        norm = math.sqrt(float(np.dot(vector, vector)))
        if norm > 0:
            vector /= norm
        return vector

    def _load_model(self):
        if self.model is not None or self.use_local_fallback:
            return

        try:
            from sentence_transformers import SentenceTransformer

            local_model_path = settings.EMBEDDING_MODEL_PATH.strip()
            if local_model_path:
                model_source = Path(local_model_path)
                if not model_source.is_absolute():
                    model_source = Path(__file__).resolve().parents[2] / model_source
                if model_source.exists():
                    self.model = SentenceTransformer(
                        str(model_source),
                        local_files_only=True,
                    )
                    self.dimension = int(
                        getattr(
                            self.model,
                            "get_sentence_embedding_dimension",
                            lambda: 384,
                        )()
                        or 384
                    )
                    return

            default_local_model = (
                Path(__file__).resolve().parents[2]
                / "models"
                / "paraphrase-multilingual-MiniLM-L12-v2"
            )
            if default_local_model.exists():
                self.model = SentenceTransformer(
                    str(default_local_model),
                    local_files_only=True,
                )
                self.dimension = int(
                    getattr(
                        self.model,
                        "get_sentence_embedding_dimension",
                        lambda: 384,
                    )()
                    or 384
                )
                return

            self.model = SentenceTransformer(self.model_name, local_files_only=True)
            self.dimension = int(
                getattr(self.model, "get_sentence_embedding_dimension", lambda: 384)()
                or 384
            )
        except Exception:
            self.use_local_fallback = True
            self.dimension = 384

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9_]+", text.lower())

    def _hash_embed(self, text: str) -> np.ndarray:
        return self._hash_embed_with_dimension(text, self.dimension)

    async def _embed_via_api(self, texts: List[str]) -> np.ndarray:
        response = await self.embedding_client.embeddings.create(
            model=settings.EMBEDDING_MODEL_NAME,
            input=texts,
        )
        vectors = np.array([item.embedding for item in response.data], dtype="float32")
        if vectors.size == 0:
            raise ValueError("Embedding API returned empty vectors.")
        return vectors

    async def _embed_texts(self, texts: List[str]) -> np.ndarray:
        provider = settings.EMBEDDING_PROVIDER.lower()
        if provider in {"siliconflow", "deepseek", "openai"}:
            try:
                return await self._embed_via_api(texts)
            except Exception:
                pass

        self._load_model()
        if self.model is not None:
            return self.model.encode(texts, convert_to_numpy=True).astype("float32")
        return np.vstack([self._hash_embed(text) for text in texts]).astype("float32")

    def _split_text(self, text: str, max_chars: int = 900) -> List[str]:
        cleaned = text.replace("\r\n", "\n").strip()
        if not cleaned:
            return []

        paragraphs = [item.strip() for item in cleaned.split("\n") if item.strip()]
        chunks: List[str] = []
        current = ""
        for paragraph in paragraphs:
            if len(current) + len(paragraph) + 1 <= max_chars:
                current = f"{current}\n{paragraph}".strip()
            else:
                if current:
                    chunks.append(current)
                current = paragraph
        if current:
            chunks.append(current)
        return chunks or [cleaned[:max_chars]]

    def _read_chunks(self, file_path: str) -> List[Dict]:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            chunks: List[Dict] = []
            with open(path, "rb") as file_obj:
                pdf_reader = PyPDF2.PdfReader(file_obj)
                for page_index, page in enumerate(pdf_reader.pages, start=1):
                    text = (page.extract_text() or "").strip()
                    for chunk in self._split_text(text):
                        chunks.append(
                            {
                                "text": chunk,
                                "metadata": {
                                    "page": page_index,
                                    "source": path.name,
                                    "file_path": str(path),
                                },
                            }
                        )
            return chunks

        if suffix == ".docx":
            doc = DocxDocument(file_path)
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")

        return [
            {
                "text": chunk,
                "metadata": {
                    "page": 1,
                    "source": path.name,
                    "file_path": str(path),
                },
            }
            for chunk in self._split_text(text)
        ]

    async def create_embeddings(self, file_path: str) -> Dict:
        text_chunks = self._read_chunks(file_path)
        if not text_chunks:
            raise ValueError("未能从文档中提取可用文本内容。")

        vectors = await self._embed_texts([item["text"] for item in text_chunks])
        self.dimension = int(vectors.shape[1])
        index = self._create_index(self.dimension)
        index.add(vectors)

        file_hash = hashlib.md5(file_path.encode("utf-8")).hexdigest()
        index_id = f"index_{file_hash}"
        documents = {
            str(i): {
                "text": item["text"],
                "metadata": item["metadata"],
            }
            for i, item in enumerate(text_chunks)
        }

        self._save_index(file_hash, index, documents)
        return {"status": "success", "index_id": index_id, "chunks": len(text_chunks)}

    def _save_index(self, file_id: str, index: faiss.Index, documents: dict):
        index_path = self.index_dir / f"index_{file_id}.bin"
        docs_path = self.index_dir / f"docs_{file_id}.json"
        faiss.write_index(index, str(index_path))
        with open(docs_path, "w", encoding="utf-8") as file_obj:
            json.dump(documents, file_obj, ensure_ascii=False, indent=2)

    def _load_index(self, index_id: str):
        file_id = index_id.replace("index_", "")
        index_path = self.index_dir / f"index_{file_id}.bin"
        docs_path = self.index_dir / f"docs_{file_id}.json"

        if not index_path.exists() or not docs_path.exists():
            raise FileNotFoundError(f"找不到知识库索引文件: {index_id}")

        self.current_index = faiss.read_index(str(index_path))
        self.dimension = int(self.current_index.d)

        with open(docs_path, "r", encoding="utf-8") as file_obj:
            self.current_documents = json.load(file_obj)
        if not self.current_documents:
            raise ValueError("知识库索引为空。")

    async def search(self, query: str, top_k: int = 3) -> List[dict]:
        if self.current_index is None:
            raise ValueError("索引尚未加载。")

        index_dimension = int(self.current_index.d)
        query_vector = await self._embed_texts([query])
        query_dimension = int(query_vector.shape[1])
        if query_dimension != index_dimension:
            if index_dimension == 384:
                query_vector = np.vstack(
                    [self._hash_embed_with_dimension(query, index_dimension)]
                ).astype("float32")
            else:
                raise ValueError(
                    "当前查询向量与旧文档索引的维度不一致。请删除当前文档并重新上传，"
                    "用新的 embedding 配置重建索引后再提问。"
                )

        distances, indices = self.current_index.search(query_vector, top_k)

        results = []
        for i in range(len(indices[0])):
            idx_str = str(int(indices[0][i]))
            if idx_str in self.current_documents:
                results.append(
                    {
                        "score": float(distances[0][i]),
                        "content": self.current_documents[idx_str]["text"],
                        "metadata": self.current_documents[idx_str]["metadata"],
                    }
                )
        return results

    async def search_index(self, index_id: str, query: str, top_k: int = 3) -> List[dict]:
        self._load_index(index_id)
        return await self.search(query, top_k=top_k)
