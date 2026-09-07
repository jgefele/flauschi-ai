from collections.abc import Callable
from urllib.parse import urlparse

import dagster as dg
import requests
from boto3.s3.transfer import TransferConfig
from botocore.response import StreamingBody
from dagster_aws.s3 import S3Resource
from types_boto3_s3 import S3Client

from flauschi_pipeline.defs.common import episode_partition
from flauschi_pipeline.models import AudioArchiveMetadata, EpisodeMetadata


def _content_length(response: requests.Response) -> int | None:
    try:
        return int(response.headers["Content-Length"])
    except (KeyError, ValueError):
        return None


def _build_public_url(s3_client: S3Client, bucket: str, key: str) -> str:
    parsed = urlparse(s3_client.meta.endpoint_url)
    clean_key = key.lstrip("/")
    return f"{parsed.scheme}://{bucket}.{parsed.netloc}/{clean_key}"


# B2 requires every non-final multipart part to be at least 5 MiB
B2_CHUNK_SIZE = 5 * 1024 * 1024


def archive_url_to_s3(
    url: str,
    s3_client: S3Client,
    bucket: str,
    key: str,
    chunksize: int = B2_CHUNK_SIZE,
    callback: Callable[[int, int], None] | None = None,
) -> AudioArchiveMetadata:
    with requests.get(url, stream=True, timeout=(10, 60)) as response:
        response.raise_for_status()

        size = _content_length(response)
        metadata: dict = {"source_url": url}
        metadata["redirected_url"] = response.url if response.history else None
        extra_args: dict = {"Metadata": metadata}
        if content_type := response.headers.get("Content-Type"):
            metadata["content_type"] = content_type
            extra_args["ContentType"] = content_type

        transferred_sum = 0

        def _callback(transferred: int):
            if callback:
                nonlocal transferred_sum
                transferred_sum += transferred
                callback(transferred_sum, size or 0)

        with StreamingBody(response.raw, size) as file_stream:  # pyright: ignore[reportArgumentType]
            s3_client.upload_fileobj(
                file_stream,
                bucket,
                key,
                ExtraArgs=extra_args,
                Config=TransferConfig(
                    multipart_threshold=chunksize,
                    multipart_chunksize=chunksize,
                    use_threads=False,
                ),
                Callback=_callback,
            )
            # Content-Length might have been missing -> use actual size from stream
            size = file_stream.tell()

    return AudioArchiveMetadata(
        **metadata,
        file_size=size,
        archive_url=_build_public_url(s3_client, bucket, key),
    )


@dg.asset(
    pool="large_s3_upload",
    partitions_def=episode_partition,
)
def audio_archive(
    context: dg.AssetExecutionContext,
    episode_metadata: EpisodeMetadata,
    s3: S3Resource,
) -> AudioArchiveMetadata:
    url = episode_metadata.audio_url
    s3_client: S3Client = s3.get_client()

    if not (bucket := dg.EnvVar("S3_BUCKET").get_value()):
        raise dg.Failure("S3_BUCKET not configured")

    def _logging_callback(transferred: int, total: int):
        context.log.info(f"{transferred} of {total} bytes transferred")

    return archive_url_to_s3(
        url,
        s3_client,
        bucket,
        f"audio/{episode_metadata.slug}.mp3",
        callback=_logging_callback,
    )
