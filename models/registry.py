"""
模型注册表 - 管理模型版本、元数据和部署
"""

import json
import pickle  # nosec B403
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from apps.api.core.settings import settings

logger = structlog.get_logger()
# settings imported above


@dataclass
class ModelMetadata:
    """模型元数据"""

    model_id: str
    version: str
    name: str
    description: str
    framework: str  # xgboost, sklearn等

    # 性能指标
    accuracy: float
    precision: float
    recall: float
    f1_score: float

    # 训练信息
    training_date: datetime
    training_duration: float
    training_samples: int
    feature_count: int

    # 文件路径
    model_path: str
    metadata_path: str

    # 其他信息
    created_by: str = "system"
    tags: list[str] | None = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class ModelVersion:
    """模型版本"""

    version: str
    metadata: ModelMetadata
    is_active: bool = False
    deployment_date: datetime | None = None


class ModelRegistry:
    """模型注册表"""

    def __init__(self, registry_path: str | None = None):
        """
        初始化模型注册表

        Args:
            registry_path: 注册表根目录
        """
        self.registry_path = Path(registry_path or settings.model_registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)

        # 注册表索引文件
        self.index_file = self.registry_path / "registry_index.json"
        self._load_index()

    def _load_index(self) -> None:
        """加载注册表索引"""
        if self.index_file.exists():
            with open(self.index_file) as f:
                self.index = json.load(f)
        else:
            self.index = {
                "models": {},  # model_id -> list of versions
                "active_versions": {},  # model_id -> active_version
                "created_date": datetime.now().isoformat(),
            }
            self._save_index()

    def _save_index(self) -> None:
        """保存注册表索引"""
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2, default=str)

    def register_model(
        self,
        model: Any,
        metadata: ModelMetadata,
        make_active: bool = True,  # 训练好的模型对象
    ) -> str:
        """
        注册新模型版本

        Args:
            model: 训练好的模型对象
            metadata: 模型元数据
            make_active: 是否设为活跃版本

        Returns:
            模型版本ID
        """
        model_id = metadata.model_id
        version = metadata.version

        logger.info(
            "注册新模型版本",
            model_id=model_id,
            version=version,
            make_active=make_active,
        )

        # 创建模型目录
        model_dir = self.registry_path / model_id / version
        model_dir.mkdir(parents=True, exist_ok=True)

        # 保存模型文件
        model_file = model_dir / "model.pkl"
        with open(model_file, "wb") as f:
            pickle.dump(model, f)

        # 更新文件路径
        metadata.model_path = str(model_file)
        metadata.metadata_path = str(model_dir / "metadata.json")

        # 保存元数据
        with open(metadata.metadata_path, "w") as f:
            json.dump(asdict(metadata), f, indent=2, default=str)

        # 更新索引
        if model_id not in self.index["models"]:
            self.index["models"][model_id] = []

        version_info = {
            "version": version,
            "metadata_path": metadata.metadata_path,
            "registration_date": datetime.now().isoformat(),
            "is_active": make_active,
        }

        self.index["models"][model_id].append(version_info)

        # 设置活跃版本
        if make_active:
            self._set_active_version(model_id, version)

        self._save_index()

        logger.info(
            "模型注册成功",
            model_id=model_id,
            version=version,
            model_path=str(model_file),
        )

        return f"{model_id}:{version}"

    def _set_active_version(self, model_id: str, version: str) -> None:
        """设置活跃版本"""
        # 取消其他版本的活跃状态
        if model_id in self.index["models"]:
            for v_info in self.index["models"][model_id]:
                v_info["is_active"] = False

        # 设置新的活跃版本
        for v_info in self.index["models"][model_id]:
            if v_info["version"] == version:
                v_info["is_active"] = True
                v_info["deployment_date"] = datetime.now().isoformat()
                break

        self.index["active_versions"][model_id] = version

    def load_model(self, model_id: str, version: str | None = None) -> Any:
        """
        加载模型

        Args:
            model_id: 模型ID
            version: 模型版本,None表示加载活跃版本

        Returns:
            模型对象
        """
        if version is None:
            version = self.get_active_version(model_id)
            if version is None:
                raise ValueError(f"模型 {model_id} 没有活跃版本")

        # 查找模型文件
        model_path = None
        if model_id in self.index["models"]:
            for v_info in self.index["models"][model_id]:
                if v_info["version"] == version:
                    metadata_path = v_info["metadata_path"]
                    with open(metadata_path) as f:
                        metadata = json.load(f)
                    model_path = metadata["model_path"]
                    break

        if model_path is None or not Path(model_path).exists():
            raise FileNotFoundError(f"找不到模型文件: {model_id}:{version}")

        # 加载模型
        with open(model_path, "rb") as f:
            model = pickle.load(f)  # nosec B301

        logger.info("模型加载成功", model_id=model_id, version=version)
        return model

    def get_active_version(self, model_id: str) -> str | None:
        """获取活跃版本"""
        return self.index["active_versions"].get(model_id)

    def list_models(self) -> dict[str, list[str]]:
        """列出所有模型和版本"""
        result = {}
        for model_id, versions in self.index["models"].items():
            result[model_id] = [v["version"] for v in versions]
        return result

    def get_model_metadata(self, model_id: str, version: str) -> ModelMetadata:
        """获取模型元数据"""
        metadata_path = None
        if model_id in self.index["models"]:
            for v_info in self.index["models"][model_id]:
                if v_info["version"] == version:
                    metadata_path = v_info["metadata_path"]
                    break

        if metadata_path is None:
            raise ValueError(f"找不到模型版本: {model_id}:{version}")

        with open(metadata_path) as f:
            metadata_dict = json.load(f)

        # 转换日期字符串
        if isinstance(metadata_dict["training_date"], str):
            metadata_dict["training_date"] = datetime.fromisoformat(
                metadata_dict["training_date"]
            )

        return ModelMetadata(**metadata_dict)

    def delete_model_version(self, model_id: str, version: str) -> None:
        """删除模型版本"""
        if model_id not in self.index["models"]:
            raise ValueError(f"模型不存在: {model_id}")

        # 检查是否是活跃版本
        if self.get_active_version(model_id) == version:
            raise ValueError(f"无法删除活跃版本: {model_id}:{version}")

        # 删除文件
        model_dir = self.registry_path / model_id / version
        if model_dir.exists():
            import shutil

            shutil.rmtree(model_dir)

        # 更新索引
        self.index["models"][model_id] = [
            v for v in self.index["models"][model_id] if v["version"] != version
        ]

        self._save_index()

        logger.info("模型版本已删除", model_id=model_id, version=version)

    def promote_model(self, model_id: str, version: str) -> None:
        """提升模型版本为活跃版本"""
        if model_id not in self.index["models"]:
            raise ValueError(f"模型不存在: {model_id}")

        # 检查版本是否存在
        version_exists = False
        for v_info in self.index["models"][model_id]:
            if v_info["version"] == version:
                version_exists = True
                break

        if not version_exists:
            raise ValueError(f"模型版本不存在: {model_id}:{version}")

        old_active = self.get_active_version(model_id)
        self._set_active_version(model_id, version)
        self._save_index()

        logger.info(
            "模型版本已提升",
            model_id=model_id,
            old_version=old_active,
            new_version=version,
        )

    def get_registry_stats(self) -> dict[str, Any]:
        """获取注册表统计信息"""
        stats = {
            "total_models": len(self.index["models"]),
            "total_versions": sum(
                len(versions) for versions in self.index["models"].values()
            ),
            "active_models": len(self.index["active_versions"]),
            "registry_path": str(self.registry_path),
            "created_date": self.index["created_date"],
        }

        return stats
