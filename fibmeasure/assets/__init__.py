from pathlib import Path
import yaml


ASSETS_ROOT = Path(__file__).absolute().parent


with open(ASSETS_ROOT / 'transform_views.yaml', 'r', encoding='utf-8') as file:
    TRANSFORM_VIEW_ASSETS = yaml.safe_load(file)
