"""CLI helper to run telemetry pre-processing and write merged CSV"""
import argparse
from grracing.preprocess import merge_lap_and_telemetry

parser = argparse.ArgumentParser()
parser.add_argument('--lap', required=True, help='path to lap_time CSV')
parser.add_argument('--telemetry', required=True, help='path to telemetry CSV')
parser.add_argument('--out', default='models/merged_lap_telemetry.csv')
args = parser.parse_args()

merged = merge_lap_and_telemetry(args.lap, args.telemetry, out_csv=args.out)
print('Wrote merged CSV to', args.out)
