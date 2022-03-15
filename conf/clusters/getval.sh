databricks clusters list --output JSON | jq '[ .clusters[] | select(.default_tags.ClusterName==rocinante) .cluster_id ]'
