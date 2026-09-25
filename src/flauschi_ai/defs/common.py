import dagster as dg

episode_partition = dg.DynamicPartitionsDefinition(name="episode")
