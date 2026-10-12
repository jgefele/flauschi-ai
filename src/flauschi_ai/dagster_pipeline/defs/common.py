import dagster as dg

episode_partition = dg.DynamicPartitionsDefinition(name="episode")


# like on_missing but also consider partitions that were added to the asset before the condition was enabled.
# see https://dagster.io/docs/guides/automate/declarative-automation/customizing-automation-conditions/customizing-on-missing-condition
on_missing_with_unlimited_backfill = dg.AutomationCondition.on_missing().replace(
    "handled",
    dg.AutomationCondition.newly_requested() | dg.AutomationCondition.newly_updated(),
)
