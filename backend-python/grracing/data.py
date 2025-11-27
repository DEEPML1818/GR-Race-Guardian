import pandas as pd

def load_telemetry(csv_path, nrows=None):
    """Load a telemetry / lap-time CSV into a pandas DataFrame.

    This loader attempts to be robust for the various CSVs in the workspace.
    """
    df = pd.read_csv(csv_path, nrows=nrows)
    return df
