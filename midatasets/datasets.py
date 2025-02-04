import datetime
import os
from typing import Optional, Dict, Union

from loguru import logger

from midatasets import configs
from midatasets.MIReader import MIReader
from midatasets.databases import DBBase, MIDatasetDBTypes, MIDatasetModel
from midatasets.storage_backends import DatasetS3Backend, DatasetLocalBackend

_midataset_store = None


def get_db(db: Optional[Union[DBBase, str]] = None) -> DBBase:
    if isinstance(db, DBBase):
        return db
    elif isinstance(db, str):
        return MIDatasetDBTypes[db].value()
    else:
        return MIDatasetDBTypes[configs.database].value()


class MIDatasetStore:
    def __init__(self, db: Optional[Union[DBBase, str]] = None):
        self._db: DBBase = get_db(db)

    def get_info_all(self, selector: Optional[Dict] = None, names_only: bool = False):
        datasets = self._db.find_all(selector=selector)
        if names_only:
            return [d["name"] for d in datasets]
        else:
            return datasets

    def get_info(self, name: str):
        return self._db.find(selector={"name": name})

    def get_storage_backend(self, name, remote: bool = False):
        info = self.get_info(name)
        # TODO: make this more generic
        if remote:
            return DatasetS3Backend(prefix=info['aws_s3_prefix'], bucket=info['aws_s3_bucket'])
        else:
            return DatasetLocalBackend(root_path=f"{os.path.expandvars(configs.root_path)}/{name}")

    def create(self, dataset: MIDatasetModel):
        return self._db.create(item=dataset)

    def delete(self, name: str):
        res = self._db.delete({"name": name})
        try:
            if res > 0:
                logger.info(f"deleted {name}")
            else:
                logger.error(f"{name} not found for deletion")
        except:
            pass
        return res

    def update(self, name: str, attributes: Dict):
        if "modified_time" not in attributes:
            attributes["modified_time"] = datetime.datetime.now().isoformat()
        return self._db.update(selector={"name": name}, item=attributes)

    def get_local_path(self, name: str):
        dataset = self.get_info(name)
        path = os.path.join(
            configs.root_path, dataset.get("subpath", None) or dataset["name"]
        )
        return os.path.expandvars(path)

    def load(self, name: str, spacing=0, **kwargs) -> MIReader:
        dataset = self.get_info(name)
        dataset["spacing"] = spacing
        dataset["dir_path"] = os.path.join(
            configs.root_path, dataset.get("subpath", None) or dataset["name"]
        )
        dataset.update(kwargs)
        return MIReader.from_dict(**dataset)


def get_midataset_store():
    global _midataset_store
    if _midataset_store is None:
        _midataset_store = MIDatasetStore()
    return _midataset_store


def set_midataset_store(db):
    global _midataset_store
    _midataset_store = db


def _load_dataset_from_db(name, **kwargs) -> MIReader:
    dataset = get_midataset_store().get_info(name)
    if dataset is None:
        raise Exception(f'Dataset {name} not found')

    dataset["dir_path"] = os.path.join(
        configs.root_path, dataset.get("subpath", None) or dataset["name"]
    )
    dataset.update(kwargs)
    return MIReader.from_dict(**dataset)


def load_dataset(name, spacing=0, dataset_path=None, **kwargs) -> MIReader:
    if dataset_path:
        return MIReader(name=name, spacing=spacing, dir_path=dataset_path, **kwargs)
    else:
        return _load_dataset_from_db(name, spacing=spacing, **kwargs)
