import json


def load_minutes_record(minutes_id):
    minutes_fp = f'./out/minutes/{minutes_id}.json'
    return load_json(minutes_fp)


def load_gclip_record(gclip_id):
    gclip_fp = f'./out/gclip/{gclip_id}.json'
    return load_json(gclip_fp)


def load_json(fp):
    with open(fp, 'r') as f:
        data = json.load(f)
    return data
