"""
Universal YAML → draw.io diagram generator.

Reads .yaml descriptor files and produces .drawio XML + PNG export.
Supports two diagram types:
  - architecture: groups, boxes, cylinders, native shapes, connections
  - bpmn: swimlanes, tasks, events, gateways, flows (native mxgraph.bpmn.*)

Usage:
    python diagram_generator.py                      # all YAML files in diagrams_yaml/
    python diagram_generator.py diagrams_yaml/N01.yaml  # single file
    python diagram_generator.py diagrams_yaml/N0*.yaml  # glob pattern
"""
import os, sys, glob, subprocess, yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from create_drawio_diagrams import DrawioBuilder, C
from create_bpmn_diagrams_v2 import (
    BPMNDiagram, LANE_COLORS,
    C_USR, C_SVC, C_MAN, C_SND, C_START, C_END, C_INTER, C_GW, C_NOTE,
    _gw_label, _lbl,
    LANE_H, LANE_HDR, TASK_W, TASK_H, GW_SZ, EV_SZ
)

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
YAML_DIR = os.path.join(WORK_DIR, 'diagrams_yaml')
OUT_DIR = os.path.join(WORK_DIR, 'diagrams_output')
os.makedirs(OUT_DIR, exist_ok=True)


def export_png(drawio_path):
    """Export .drawio to .png via draw.io Desktop CLI."""
    png = drawio_path.replace('.drawio', '.png')
    r = subprocess.run(
        ['DrawIO.exe', '--export', '--format', 'png', '--scale', '2',
         '--output', png, drawio_path],
        capture_output=True, text=True, timeout=90)
    if os.path.exists(png):
        sz = os.path.getsize(png)
        print(f"    PNG: {os.path.basename(png)} ({sz:,} bytes)")
        return True
    else:
        print(f"    PNG FAILED: {r.stderr[:300]}")
        return False


# ════════════════════════════════════════════════════════════
# Architecture diagram generator
# ════════════════════════════════════════════════════════════
def generate_architecture(spec, out_path):
    """Generate architecture diagram from YAML spec."""
    meta = spec.get('meta', {})
    d = DrawioBuilder(
        meta.get('title', 'Diagram'),
        meta.get('page_w', 1200),
        meta.get('page_h', 850))

    if meta.get('title'):
        d.title(f"<b>{meta['title']}</b>",
                meta.get('title_x', 200), meta.get('title_y', 5),
                meta.get('title_w', 850), 35)
    if meta.get('subtitle'):
        d.subtitle(meta['subtitle'],
                   meta.get('title_x', 200), meta.get('title_y', 5) + 33,
                   meta.get('title_w', 850), 22)

    ids = {}  # id -> cell_id mapping

    for el in spec.get('elements', []):
        eid = el.get('id', '')
        kind = el['kind']
        label = el.get('label', '')
        color = C.get(el.get('color', 'blue'), C['blue'])
        extra = el.get('extra')
        pos = el.get('pos', el.get('rect', [0, 0, 100, 60]))
        x, y, w, h = pos[0], pos[1], pos[2], pos[3]

        if kind == 'group':
            cid = d.group(label, x, y, w, h, color, extra)
        elif kind == 'box':
            cid = d.box(label, x, y, w, h, color, extra)
        elif kind == 'cylinder':
            cid = d.cylinder(label, x, y, w, h, color)
        elif kind == 'diamond':
            cid = d.diamond(label, x, y, w, h, color)
        elif kind == 'hexagon':
            cid = d.hexagon(label, x, y, w, h, color)
        elif kind == 'cloud':
            cid = d.cloud(label, x, y, w, h, color)
        elif kind == 'native':
            ref = el['ref']
            cid = d.native(label, x, y, w, h, ref, color, extra)
        elif kind == 'title':
            cid = d.title(label, x, y, w, h)
        elif kind == 'subtitle':
            cid = d.subtitle(label, x, y, w, h)
        elif kind == 'header':
            cid = d.header(label, x, y, w, h, color)
        else:
            print(f"    WARNING: unknown kind '{kind}' for element '{eid}'")
            continue

        if eid:
            ids[eid] = cid

    for conn in spec.get('connections', []):
        src = ids.get(conn['from'], conn['from'])
        tgt = ids.get(conn['to'], conn['to'])
        label = conn.get('label', '')
        dashed = conn.get('dashed', False)
        direction = conn.get('direction', 'tb')  # tb or lr
        color = conn.get('color', '#666666')
        exit_xy = tuple(conn['exit_xy']) if conn.get('exit_xy') else None
        entry_xy = tuple(conn['entry_xy']) if conn.get('entry_xy') else None
        waypoints = [tuple(p) for p in conn['waypoints']] if conn.get('waypoints') else None

        if direction == 'lr':
            d.connect_lr(src, tgt, label, color, dashed, exit_xy, entry_xy, waypoints)
        else:
            d.connect(src, tgt, label, color, dashed, exit_xy, entry_xy, waypoints)

    d.save(out_path)


# ════════════════════════════════════════════════════════════
# BPMN diagram generator
# ════════════════════════════════════════════════════════════

# Task color mapping
_TASK_COLORS = {
    'user_task': C_USR, 'service_task': C_SVC,
    'manual_task': C_MAN, 'send_task': C_SND,
    'script_task': C_SVC, 'rule_task': C_SVC,
}
# Task marker mapping
_TASK_MARKERS = {
    'user_task': 'user', 'service_task': 'service',
    'manual_task': 'manual', 'send_task': 'send',
    'script_task': 'script', 'rule_task': 'businessRule',
}
# Event type mapping
_EVENT_MAP = {
    'start':         ('standard', 'general', C_START),
    'end':           ('end', 'terminate2', C_END),
    'end_error':     ('end', 'error', C_END),
    'end_terminate': ('end', 'terminate2', C_END),
    'timer':         ('catching', 'timer', C_INTER),
    'message_catch': ('catching', 'message', C_INTER),
    'message_throw': ('throwing', 'message', C_INTER),
}
# Gateway type mapping
_GW_MAP = {
    'xor': 'exclusive', 'parallel_gw': 'parallel', 'inclusive_gw': 'inclusive',
}


def generate_bpmn(spec, out_path):
    """Generate BPMN diagram from YAML spec."""
    meta = spec.get('meta', {})
    lanes_def = spec.get('lanes', [])
    lane_tuples = [(l['name'], l['color']) for l in lanes_def]
    lane_names = [l['name'] for l in lanes_def]

    bp = BPMNDiagram(
        meta.get('title', 'BPMN'),
        meta.get('subtitle', ''),
        width=meta.get('page_w', 1600),
        lane_defs=lane_tuples)

    ids = {}

    for el in spec.get('elements', []):
        eid = el.get('id', '')
        kind = el['kind']
        lane = lane_names[el['lane']] if isinstance(el.get('lane'), int) else el.get('lane', '')
        x = el.get('x', 0)
        label = el.get('label', '')
        w = el.get('w')

        cid = None

        if kind in _TASK_MARKERS:
            marker = _TASK_MARKERS[kind]
            colors = _TASK_COLORS[kind]
            cid = bp._task(lane, x, label, marker, colors, w)

        elif kind in _EVENT_MAP:
            outline, symbol, colors = _EVENT_MAP[kind]
            cid = bp._event(lane, x, label, outline, symbol, colors)

        elif kind in _GW_MAP:
            gwType = _GW_MAP[kind]
            cid = bp._gateway(lane, x, gwType, label)

        elif kind == 'gw_label':
            color = el.get('color', '#F57F17')
            direction = el.get('dir', 'right')
            _gw_label(bp, lane, x, label, color, direction)

        elif kind == 'label_at':
            lx = el.get('abs_x', 0)
            ly = el.get('abs_y', 0)
            color = el.get('color', '#666666')
            bp.label_at(lx, ly, label, color)

        elif kind == 'annotation':
            ax = el.get('abs_x', 0)
            ay = el.get('abs_y', 0)
            aw = el.get('w', 180)
            ah = el.get('h', 55)
            cid = bp.annotation(ax, ay, label, aw, ah)

        elif kind == 'box':
            # Allow placing boxes (e.g., notes) in BPMN
            pos = el.get('pos', [0, 0, 100, 40])
            color = C.get(el.get('color', 'white'), C['white'])
            extra = el.get('extra')
            cid = bp.d.box(label, pos[0], pos[1], pos[2], pos[3], color, extra)

        else:
            print(f"    WARNING: unknown BPMN kind '{kind}' for '{eid}'")
            continue

        if eid and cid:
            ids[eid] = cid

    for conn in spec.get('connections', []):
        src = ids.get(conn['from'], conn['from'])
        tgt = ids.get(conn['to'], conn['to'])
        label = conn.get('label', '')
        flow_type = conn.get('type', 'flow')

        exit_xy = tuple(conn['exit_xy']) if conn.get('exit_xy') else None
        entry_xy = tuple(conn['entry_xy']) if conn.get('entry_xy') else None
        waypoints = [tuple(p) for p in conn['waypoints']] if conn.get('waypoints') else None
        label_x = conn.get('label_x')
        label_y = conn.get('label_y')

        if flow_type == 'msg_flow':
            bp.msg_flow(src, tgt, label, exit_xy, entry_xy, waypoints)
        else:
            bp.flow(src, tgt, label, exit_xy, entry_xy, label_x, label_y, waypoints)

    bp.d.save(out_path)


# ════════════════════════════════════════════════════════════
# Main dispatcher
# ════════════════════════════════════════════════════════════
def process_yaml(yaml_path):
    """Read a YAML descriptor and generate .drawio + .png."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    basename = os.path.splitext(os.path.basename(yaml_path))[0]
    out_path = os.path.join(OUT_DIR, f"{basename}.drawio")
    diagram_type = spec.get('type', 'architecture')

    print(f"  [{diagram_type.upper()}] {basename}")

    if diagram_type == 'bpmn':
        generate_bpmn(spec, out_path)
    else:
        generate_architecture(spec, out_path)

    export_png(out_path)


def main():
    if len(sys.argv) > 1:
        # Process specific files (supports glob)
        files = []
        for arg in sys.argv[1:]:
            files.extend(glob.glob(arg))
    else:
        # Process all YAML files in diagrams_yaml/
        files = sorted(glob.glob(os.path.join(YAML_DIR, '*.yaml')))

    if not files:
        print("No YAML files found.")
        return

    print("=" * 60)
    print(f"Generating {len(files)} diagram(s)...")
    print("=" * 60)

    for fp in files:
        process_yaml(fp)

    print("=" * 60)
    print(f"Done! {len(files)} diagram(s) generated in {OUT_DIR}")


if __name__ == '__main__':
    main()
