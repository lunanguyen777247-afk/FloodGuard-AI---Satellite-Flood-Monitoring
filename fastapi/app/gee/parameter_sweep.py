#!/usr/bin/env python3
"""
Parameter sweep helper to tune threshold parameters for flood detection.

Usage:
  PYTHONPATH=fastapi python fastapi/app/gee/parameter_sweep.py --region "Quang Tri" --start 2024-08-15 --end 2024-08-22 --ground_truth path/to/gt.geojson

If no ground-truth provided, the script will use JRC permanent water as a weak proxy
and report relative changes.
"""
import ee
import argparse
import json
import os
from datetime import datetime

# Initialize GEE using project .env like other scripts if needed
# This script expects your FASTAPI env to be available or GEE already initialized

PARAM_GRID = {
    'vv': [-20, -17.5, -15, -12.5, -10],
    'ratio': [-4, -3, -2, -1, 0],
    'k': [0.25, 0.5, 0.75]
}


def iou_from_vectors(pred_mask, gt_fc, region, scale=30):
    # Compute area intersection / union between pred_mask and gt geometry
    pixel_area = ee.Image.pixelArea()
    pred = pred_mask.rename('pred')
    gt = gt_fc.reduceToImage(properties=['value'], reducer=ee.Reducer.first()).gt(0).rename('gt') if isinstance(gt_fc, ee.FeatureCollection) else None
    if gt is None:
        return None
    inter = pred.And(gt).multiply(pixel_area).reduceRegion(ee.Reducer.sum(), geometry=region, scale=scale, maxPixels=1e10).get('pred')
    union = pred.Or(gt).multiply(pixel_area).reduceRegion(ee.Reducer.sum(), geometry=region, scale=scale, maxPixels=1e10).get('pred')
    inter_v = inter.getInfo() or 0
    union_v = union.getInfo() or 0
    if union_v == 0:
        return 0.0
    return inter_v / union_v


def load_ground_truth(path):
    with open(path, 'r') as fh:
        return json.load(fh)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', required=True)
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--ground_truth', required=False)
    parser.add_argument('--scale', type=int, default=30)
    args = parser.parse_args()

    # Init ee: load service account credentials from fastapi/.env if available
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        root = Path(__file__).parents[2]
        env_path = root / 'fastapi' / '.env' if (root / 'fastapi' / '.env').exists() else root / '.env'
        load_dotenv(env_path)
        service_account = os.getenv('GEE_SERVICE_ACCOUNT')
        key_path = os.getenv('GEE_PRIVATE_KEY_PATH')
        if service_account and key_path:
            if not Path(key_path).is_absolute():
                # key path is relative to repository root or fastapi folder
                potential = Path(__file__).parents[3] / key_path
                if potential.exists():
                    key_path = str(potential)
                else:
                    key_path = str(root / key_path)
            credentials = ee.ServiceAccountCredentials(service_account, key_path)
            ee.Initialize(credentials)
        else:
            ee.Initialize()
    except Exception:
        ee.Initialize()

    adm1 = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM1_NAME', args.region)).first()
    try:
        region_geom = adm1.geometry()
    except Exception:
        # fallback to bounding box search
        fc = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'Viet Nam'))
        region_feat = fc.filter(ee.Filter.eq('ADM1_NAME', args.region)).first()
        try:
            region_geom = region_feat.geometry()
        except Exception:
            raise RuntimeError(f"Region geometry for {args.region} not found")

    s1 = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(region_geom).filterDate(args.start, args.end).filter(ee.Filter.eq('instrumentMode', 'IW')).filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    # try selecting VH if present
    try:
        s1 = s1.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')).select(['VV','VH'])
    except Exception:
        s1 = s1.select(['VV'])
    composite = s1.median().clip(region_geom)

    # determine if VH present in composite
    try:
        bands = composite.bandNames().getInfo()
        vh_present = 'VH' in bands
    except Exception:
        vh_present = False

    # Load GT if provided
    gt_fc = None
    if args.ground_truth:
        gt = load_ground_truth(args.ground_truth)
        gt_fc = ee.FeatureCollection(gt)

    results = []
    for vv in PARAM_GRID['vv']:
        for ratio in PARAM_GRID['ratio']:
            for k in PARAM_GRID['k']:
                vv_img = composite.select('VV')
                vh_img = composite.select('VH') if vh_present else None
                mask_vv = vv_img.lt(vv)
                mask_ratio = ee.Image(0)
                if vh_img is not None:
                    mask_ratio = vv_img.subtract(vh_img).lt(ratio)
                # compute adaptive threshold using mean - k * stdDev (server-side ee.Number)
                mean_val = vv_img.reduceRegion(ee.Reducer.mean(), region_geom, args.scale, 1e10).get('VV')
                std_val = vv_img.reduceRegion(ee.Reducer.stdDev(), region_geom, args.scale, 1e10).get('VV')
                mean_num = ee.Number(mean_val)
                std_num = ee.Number(std_val)
                adaptive_thr = mean_num.subtract(std_num.multiply(ee.Number(k)))
                adaptive = vv_img.lt(adaptive_thr)
                combined = mask_vv.Or(mask_ratio).Or(adaptive)

                score = None
                if gt_fc is not None:
                    try:
                        score = iou_from_vectors(combined.selfMask(), gt_fc, region_geom, scale=args.scale)
                    except Exception:
                        score = None

                results.append({'vv': vv, 'ratio': ratio, 'k': k, 'score': score})
                print('tested', vv, ratio, k, 'score', score)

    out = {'region': args.region, 'start': args.start, 'end': args.end, 'results': results}
    out_file = f'parameter_sweep_{args.region.replace(" ","_")}_{args.start}_{args.end}.json'
    with open(out_file, 'w') as fh:
        json.dump(out, fh, indent=2)
    print('Saved', out_file)


if __name__ == '__main__':
    main()
