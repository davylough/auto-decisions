
"""Project hooks."""
from typing import Any, Dict, Iterable, Optional
from kedro.config import ConfigLoader
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.versioning import Journal
from cms_auto_approval.pipelines.data_engineering_mumford_data import pipeline as de_m
from cms_auto_approval.pipelines.data_science_mumford_data import pipeline as ds_m
from kedro.config import TemplatedConfigLoader 


class ProjectHooks:
    @hook_impl
    def register_pipelines(self) -> Dict[str, Pipeline]:

        data_engineering_pipeline = de_m.create_pipeline()
        data_science_pipeline = ds_m.create_pipeline()

        return {
            "data_engineering": data_engineering_pipeline,
            "data_science": data_science_pipeline,
            "__default__": data_engineering_pipeline + data_science_pipeline
        }

    @hook_impl
    def register_config_loader(self, conf_paths: Iterable[str]) -> ConfigLoader:
        return TemplatedConfigLoader(
            conf_paths,
            globals_pattern="*globals.yml",  # read the globals dictionary from project config
            
        )

    @hook_impl
    def register_catalog(
        self,
        catalog: Optional[Dict[str, Dict[str, Any]]],
        credentials: Dict[str, Dict[str, Any]],
        load_versions: Dict[str, str],
        save_version: str,
        journal: Journal,
    ) -> DataCatalog:
        return DataCatalog.from_config(
            catalog, credentials, load_versions, save_version, journal
        )