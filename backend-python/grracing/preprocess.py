import pandas as pd
import os

def merge_lap_and_telemetry(lap_time_csv, telemetry_csv, out_csv=None):
    """Basic merge: reads lap_time and telemetry and aggregates telemetry per lap.

    Produces a CSV with lap fields and aggregated telemetry features (mean, max of value).
    """
    lap = pd.read_csv(lap_time_csv)
    tel = pd.read_csv(telemetry_csv)

    # try to find common vehicle identifier
    cand_ids = ['vehicle_id', 'vehicle', 'vehicle_number', 'original_vehicle_id']
    join_key = None
    for c in cand_ids:
        if c in lap.columns and c in tel.columns:
            join_key = c
            break

    if join_key is None:
        # fallback: if telemetry includes 'vehicle_id' and lap has 'vehicle_id' using different names, try heuristics
        if 'vehicle_id' in tel.columns and 'vehicle_id' in lap.columns:
            join_key = 'vehicle_id'

    # aggregate telemetry by lap and vehicle
    if 'lap' in tel.columns:
        group_cols = [join_key, 'lap'] if join_key else ['lap']
    else:
        # if telemetry has timestamp and lap has timestamp ranges, this is more complex; for now aggregate by vehicle
        group_cols = [join_key] if join_key else []

    agg = None
    if group_cols:
        # choose telemetry numeric columns to aggregate (avoid assuming a column named 'value')
        numeric_cols = tel.select_dtypes(include=['number']).columns.tolist()
        if not numeric_cols:
            # try coercing object columns to numeric and keep the ones with many numeric values
            candidate = []
            for c in tel.columns:
                coerced = pd.to_numeric(tel[c], errors='coerce')
                non_null_ratio = coerced.notna().mean()
                if non_null_ratio > 0.5:
                    candidate.append(c)
            numeric_cols = candidate

        if not numeric_cols:
            # nothing numeric to aggregate: return lap unchanged
            merged = lap
            if out_csv:
                merged.to_csv(out_csv, index=False)
            return merged

        # prepare aggregation dict for mean and max
        agg_dict = {c: ['mean', 'max'] for c in numeric_cols}
        agg = tel.groupby(group_cols).agg(agg_dict)
        # flatten columns
        agg.columns = ['_'.join(col).strip() for col in agg.columns.values]
        agg = agg.reset_index()
        # join with lap
        if join_key and 'lap' in lap.columns and 'lap' in agg.columns:
            merged = lap.merge(agg, how='left', on=[join_key, 'lap'])
        elif 'lap' in lap.columns and 'lap' in agg.columns:
            merged = lap.merge(agg, how='left', on='lap')
        elif join_key and join_key in agg.columns:
            merged = lap.merge(agg, how='left', on=join_key)
        else:
            # fallback to index-based merge
            merged = lap.merge(agg, how='left', left_index=True, right_index=True)
    else:
        # no grouping possible, return lap unchanged
        merged = lap

    if out_csv:
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)
        merged.to_csv(out_csv, index=False)

    return merged
