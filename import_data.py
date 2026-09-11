from pathlib import Path

import dagster as dg


def import_existing_assets(data_dir: str = "data"):
    instance = dg.DagsterInstance.get()

    data_path = Path(data_dir)
    if not data_path.exists() or not data_path.is_dir():
        raise FileNotFoundError(f"Directory {data_dir} does not exist.")

    events_logged = 0

    for asset in [
        "episode_metadata",
        "audio_archive",
        "assembly_ai_transcript",
        "episode",
    ]:
        asset_dir = data_path / asset
        asset_key = dg.AssetKey(asset_dir.name)

        for file_path in asset_dir.glob("*.json"):
            partition_key = file_path.stem

            event = dg.AssetMaterialization(
                asset_key=asset_key,
                partition=partition_key,
                metadata={"path": file_path.absolute()},
                description="Imported from existing data directory",
            )

            instance.report_runless_asset_event(event)
            events_logged += 1
            print(f"Logged {asset_key.to_user_string()} [partition: {partition_key}]")

    print(f"\nDone! Successfully reported {events_logged} materialization events.")


if __name__ == "__main__":
    import_existing_assets()
