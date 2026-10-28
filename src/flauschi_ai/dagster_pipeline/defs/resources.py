from typing import Any

import assemblyai as aai
import dagster as dg
from dagster_aws.s3 import S3Resource
from pydantic import BaseModel
from pydantic.v1 import BaseModel as BaseModel_v1
from upath import UPath

from flauschi_ai.constants import DATA_PATH


class PydanticUPathIOManager(dg.UPathIOManager):
    """(De)serializes pydantic models to/from JSON via UPathIOManager.

    Works with local paths and cloud storage (s3://, gs://, azure://)
    depending on the `base_path` UPath it is constructed with.
    """

    # Required: must contain a "." (asserted in UPathIOManager.__init__)
    extension: str = ".json"

    def dump_to_path(self, context: dg.OutputContext, obj: Any, path: UPath) -> None:
        if isinstance(obj, BaseModel):
            model_json = obj.model_dump_json(exclude_defaults=True)
        elif isinstance(obj, BaseModel_v1):
            model_json = obj.json(exclude_defaults=True)
        else:
            raise TypeError(
                f"PydanticUPathIOManager expected a pydantic BaseModel, got {type(obj)}. "
                + "Set the asset's return type annotation to `None` if it produces no value."
            )
        
        path.write_text(model_json, encoding="utf-8")

    def load_from_path(self, context: dg.InputContext, path: UPath) -> Any:
        model_json = path.read_text(encoding="utf-8")

        model_type = context.dagster_type.typing_type
        if isinstance(model_type, type):
            if issubclass(model_type, BaseModel):
                return model_type.model_validate_json(model_json)
            elif issubclass(model_type, BaseModel_v1):
                return model_type.parse_raw(model_json)
        raise TypeError(
            "Could not resolve a pydantic model type from the upstream annotation. "
            + "Annotate the upstream asset with `-> MyModel` or `-> Optional[MyModel]`."
        )
        

    def get_metadata(
        self, context: dg.OutputContext, obj: Any
    ) -> dict[str, dg.MetadataValue]:
        return {
            "model": dg.TextMetadataValue(
                f"{type(obj).__module__}.{type(obj).__name__}"
            ),
        }


class AssemblyAIResource(dg.ConfigurableResource):
    api_key: str

    def get_client(self) -> aai.Transcriber:
        return aai.Transcriber(client=aai.Client(api_key=self.api_key))


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "io_manager": PydanticUPathIOManager(UPath(DATA_PATH)),
            "s3": S3Resource(
                aws_access_key_id=dg.EnvVar("S3_ACCESS_KEY_ID"),
                aws_secret_access_key=dg.EnvVar("S3_SECRET_ACCESS_KEY"),
                endpoint_url=dg.EnvVar("S3_ENDPOINT_URL"),
            ),
            "aai": AssemblyAIResource(api_key=dg.EnvVar("ASSEMBLYAI_API_KEY")),
        }
    )
