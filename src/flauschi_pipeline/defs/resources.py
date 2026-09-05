from pathlib import Path
from typing import Any

import dagster as dg

from pydantic import BaseModel
from upath import UPath

from flauschi_pipeline.constants import PROJECT_PATH


class PydanticUPathIOManager(dg.UPathIOManager):
    """(De)serializes pydantic models to/from JSON via UPathIOManager.

    Works with local paths and cloud storage (s3://, gs://, azure://)
    depending on the `base_path` UPath it is constructed with.
    """

    # Required: must contain a "." (asserted in UPathIOManager.__init__)
    extension: str = ".json"

    def _resolve_model_type(
        self, context: dg.InputContext | dg.OutputContext
    ) -> type[BaseModel] | None:
        dagster_type = context.dagster_type.typing_type

        if isinstance(dagster_type, type) and issubclass(dagster_type, BaseModel):
            return dagster_type
        return None

    def dump_to_path(self, context: dg.OutputContext, obj: Any, path: UPath) -> None:
        if not isinstance(obj, BaseModel):
            raise TypeError(
                f"PydanticUPathIOManager expected a pydantic BaseModel, got {type(obj)}. "
                "Set the asset's return type annotation to `None` if it produces no value."
            )
        path.write_text(obj.model_dump_json(), encoding="utf-8")

    def load_from_path(self, context: dg.InputContext, path: UPath) -> Any:
        model_type = self._resolve_model_type(context)
        if model_type is None:
            raise TypeError(
                "Could not resolve a pydantic model type from the upstream annotation. "
                "Annotate the upstream asset with `-> MyModel` or `-> Optional[MyModel]`."
            )

        return model_type.model_validate_json(path.read_text(encoding="utf-8"))

    def get_metadata(
        self, context: dg.OutputContext, obj: Any
    ) -> dict[str, dg.MetadataValue]:
        return {
            "model": dg.TextMetadataValue(
                f"{type(obj).__module__}.{type(obj).__name__}"
            ),
        }


@dg.definitions
def resources():
    return dg.Definitions(
        # Define the I/O manager and pass it to `Definitions`
        resources={"io_manager": PydanticUPathIOManager(UPath(PROJECT_PATH / "data"))}
    )
