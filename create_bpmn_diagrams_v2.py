"""
Create 7 BPMN-standard business process diagrams for DHA Lesotho (v2).

v2 improvements over v1:
  - BPMN_02: ePassport completely reworked from P1.8 SDIS 11-stage lifecycle
  - BPMN_03: Border Control enhanced with P1.6 eBCS 5-criteria validation
  - BPMN_04: NID Card Issuance - NEW diagram from P1.3 (8-step workflow)
  - All diagrams: refined labels, improved flow routing, better annotations

Uses draw.io NATIVE BPMN shapes (mxgraph.bpmn.task / event / gateway2).
These render identically to shapes dragged from draw.io Desktop's BPMN sidebar.
No stencil catalog dependency for BPMN elements.
"""
import os
import subprocess
from create_drawio_diagrams import DrawioBuilder, C

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(WORK_DIR, 'diagrams_drawio')
os.makedirs(OUT_DIR, exist_ok=True)

DRAWIO_EXE = os.path.join(
    os.environ.get('LOCALAPPDATA', ''),
    r'Microsoft\WinGet\Packages\JGraph.Draw_Microsoft.Winget.Source_8wekyb3d8bbwe\DrawIO.exe'
)

# ============================================================
# BPMN Color Scheme
# ============================================================
LANE_COLORS = {
    'citizen':  {'fill': '#E8F5E9', 'stroke': '#2E7D32', 'font': '#1B5E20'},
    'officer':  {'fill': '#E3F2FD', 'stroke': '#1565C0', 'font': '#0D47A1'},
    'system':   {'fill': '#FFF3E0', 'stroke': '#E65100', 'font': '#BF360C'},
    'external': {'fill': '#F3E5F5', 'stroke': '#7B1FA2', 'font': '#4A148C'},
    'database': {'fill': '#E0F2F1', 'stroke': '#00695C', 'font': '#004D40'},
}

C_USR = {'fill': '#E3F2FD', 'stroke': '#1565C0', 'font': '#0D47A1'}
C_SVC = {'fill': '#FFF3E0', 'stroke': '#E65100', 'font': '#BF360C'}
C_MAN = {'fill': '#F5F5F5', 'stroke': '#616161', 'font': '#424242'}
C_SND = {'fill': '#FCE4EC', 'stroke': '#C62828', 'font': '#B71C1C'}

C_START = {'fill': '#E8F5E9', 'stroke': '#2E7D32', 'font': '#2E7D32'}
C_END   = {'fill': '#FFEBEE', 'stroke': '#C62828', 'font': '#C62828'}
C_INTER = {'fill': '#FFF3E0', 'stroke': '#E65100', 'font': '#E65100'}
C_GW = {'fill': '#FFF9C4', 'stroke': '#F57F17', 'font': '#F57F17'}
C_NOTE = {'fill': '#FAFAFA', 'stroke': '#9E9E9E', 'font': '#424242'}

EV_SZ   = 36
TASK_W  = 160
TASK_H  = 60
GW_SZ   = 44
ICON_SZ = 14
LANE_HDR = 55
LANE_H   = 160
TITLE_H  = 65


# ============================================================
# Native draw.io BPMN shape style templates
# ============================================================
# Connection points for proper edge anchoring
_PTS_EV = ("points=[[0.145,0.145,0],[0.5,0,0],[0.855,0.145,0],[1,0.5,0],"
           "[0.855,0.855,0],[0.5,1,0],[0.145,0.855,0],[0,0.5,0]];")
_PTS_GW = ("points=[[0.25,0.25,0],[0.5,0,0],[0.75,0.25,0],[1,0.5,0],"
           "[0.75,0.75,0],[0.5,1,0],[0.25,0.75,0],[0,0.5,0]];")

# Task: shape=mxgraph.bpmn.task;taskMarker={abstract|user|service|send|...}
_TASK_STYLE = ("shape=mxgraph.bpmn.task;taskMarker={marker};"
               "html=1;whiteSpace=wrap;fontSize=10;fontFamily=Helvetica;"
               "rounded=1;arcSize=10;shadow=1;"
               "fillColor={fill};strokeColor={stroke};fontColor={font};")

# Event: shape=mxgraph.bpmn.event;outline={standard|catching|throwing|end};symbol={...}
_EVENT_STYLE = (_PTS_EV +
                "shape=mxgraph.bpmn.event;html=1;fontSize=9;fontFamily=Helvetica;"
                "verticalLabelPosition=bottom;verticalAlign=top;align=center;"
                "perimeter=ellipsePerimeter;outlineConnect=0;aspect=fixed;"
                "outline={outline};symbol={symbol};"
                "fillColor={fill};strokeColor={stroke};fontColor={font};")

# Gateway: shape=mxgraph.bpmn.gateway2;gwType={exclusive|inclusive|parallel|...}
_GW_STYLE = (_PTS_GW +
             "shape=mxgraph.bpmn.gateway2;html=1;fontSize=9;fontFamily=Helvetica;"
             "verticalLabelPosition=bottom;verticalAlign=top;align=center;"
             "perimeter=rhombusPerimeter;outlineConnect=0;"
             "outline=none;symbol=none;gwType={gwType};"
             "fillColor={fill};strokeColor={stroke};fontColor={font};")


# ============================================================
# BPMNDiagram class
# ============================================================
class BPMNDiagram:
    """Builds BPMN 2.0 diagrams using draw.io native BPMN shapes.

    Uses mxgraph.bpmn.task / event / gateway2 — identical to shapes
    from draw.io Desktop's BPMN sidebar. No stencil catalog needed.
    """

    def __init__(self, title, subtitle, width=1400, lane_defs=None):
        self.width = width
        self.lane_defs = lane_defs or []
        total_h = TITLE_H + len(self.lane_defs) * LANE_H + 30
        self.d = DrawioBuilder(title, width, total_h)
        self.d.title(f"<b>{title}</b>", width // 2 - 350, 8, 700, 30)
        self.d.subtitle(subtitle, width // 2 - 350, 35, 700, 22)

        self.lane_y = {}
        y = TITLE_H
        lane_w = width - 20
        for lane_name, color_key in self.lane_defs:
            lc = LANE_COLORS[color_key]
            self.d.box("", 10, y, lane_w, LANE_H, lc,
                       ["rounded=0", "opacity=30", "strokeWidth=1"])
            self.d.box(f"<b>{lane_name}</b>", 10, y, LANE_HDR, LANE_H, lc,
                       ["rounded=0", "fontSize=9", "fontStyle=1",
                        "verticalAlign=middle", "align=center",
                        "whiteSpace=wrap", "opacity=80"])
            self.lane_y[lane_name] = y
            y += LANE_H

    def _lane_cy(self, lane_name):
        return self.lane_y[lane_name] + LANE_H // 2

    def _pos(self, lane_name, x_offset):
        x = LANE_HDR + 15 + x_offset
        cy = self._lane_cy(lane_name)
        return x, cy

    def _cell(self, label, x, y, w, h, style):
        cid = self.d._next_id()
        self.d.cells.append({
            'type': 'vertex', 'id': cid, 'parent': '1',
            'value': label, 'style': style,
            'x': x, 'y': y, 'w': w, 'h': h,
        })
        return cid

    # ── Tasks (native mxgraph.bpmn.task) ──

    def _task(self, lane, x_off, label, marker, colors, w=None):
        tw = w or TASK_W
        x, cy = self._pos(lane, x_off)
        ty = cy - TASK_H // 2
        style = _TASK_STYLE.format(
            marker=marker, fill=colors['fill'],
            stroke=colors['stroke'], font=colors['font'])
        return self._cell(label, x, ty, tw, TASK_H, style)

    def user_task(self, lane, x_off, label, w=None):
        return self._task(lane, x_off, label, "user", C_USR, w)

    def service_task(self, lane, x_off, label, w=None):
        return self._task(lane, x_off, label, "service", C_SVC, w)

    def manual_task(self, lane, x_off, label, w=None):
        return self._task(lane, x_off, label, "manual", C_MAN, w)

    def send_task(self, lane, x_off, label, w=None):
        return self._task(lane, x_off, label, "send", C_SND, w)

    def script_task(self, lane, x_off, label, w=None):
        return self._task(lane, x_off, label, "script", C_SVC, w)

    def rule_task(self, lane, x_off, label, w=None):
        return self._task(lane, x_off, label, "businessRule", C_SVC, w)

    # ── Events (native mxgraph.bpmn.event) ──

    def _event(self, lane, x_off, label, outline, symbol, colors):
        x, cy = self._pos(lane, x_off)
        style = _EVENT_STYLE.format(
            outline=outline, symbol=symbol,
            fill=colors['fill'], stroke=colors['stroke'],
            font=colors['font'])
        return self._cell(label, x, cy - EV_SZ // 2, EV_SZ, EV_SZ, style)

    def start(self, lane, x_off=0, label=""):
        return self._event(lane, x_off, label, "standard", "general", C_START)

    def end(self, lane, x_off, label=""):
        return self._event(lane, x_off, label, "end", "terminate2", C_END)

    def end_error(self, lane, x_off, label=""):
        return self._event(lane, x_off, label, "end", "error", C_END)

    def end_terminate(self, lane, x_off, label=""):
        return self._event(lane, x_off, label, "end", "terminate2", C_END)

    def timer(self, lane, x_off, label=""):
        return self._event(lane, x_off, label, "catching", "timer", C_INTER)

    def message_catch(self, lane, x_off, label=""):
        return self._event(lane, x_off, label, "catching", "message", C_INTER)

    def message_throw(self, lane, x_off, label=""):
        return self._event(lane, x_off, label, "throwing", "message", C_INTER)

    # ── Gateways (native mxgraph.bpmn.gateway2) ──

    def _gateway(self, lane, x_off, gwType, label=""):
        x, cy = self._pos(lane, x_off)
        style = _GW_STYLE.format(
            gwType=gwType, fill=C_GW['fill'],
            stroke=C_GW['stroke'], font=C_GW['font'])
        return self._cell(label, x, cy - GW_SZ // 2, GW_SZ, GW_SZ, style)

    def xor(self, lane, x_off, label=""):
        return self._gateway(lane, x_off, "exclusive", label)

    def parallel_gw(self, lane, x_off, label=""):
        return self._gateway(lane, x_off, "parallel", label)

    def inclusive_gw(self, lane, x_off, label=""):
        return self._gateway(lane, x_off, "inclusive", label)

    def label_at(self, x, y, text, color='#666666'):
        return self._cell(
            f"<span style='font-size:8px;color:{color}'>{text}</span>",
            x, y, 60, 14,
            "text;html=1;strokeColor=none;fillColor=none;align=center;"
            "verticalAlign=middle;whiteSpace=nowrap;overflow=hidden;"
            "fontFamily=Helvetica;fontSize=8;")

    def annotation(self, x, y, label, w=180, h=55):
        return self.d.box(label, x, y, w, h, C_NOTE,
                          ["fontSize=8", "rounded=0", "align=left",
                           "spacingLeft=5", "dashed=1", "dashPattern=3 3"])

    # ── Flows ──

    def flow(self, src, tgt, label="", exit_xy=None, entry_xy=None,
             label_x=None, label_y=None, waypoints=None):
        cid = self.d._next_id()
        extra = ""
        if exit_xy:
            extra += f"exitX={exit_xy[0]};exitY={exit_xy[1]};exitDx=0;exitDy=0;"
        if entry_xy:
            extra += f"entryX={entry_xy[0]};entryY={entry_xy[1]};entryDx=0;entryDy=0;"
        cell = {
            'type': 'edge', 'id': cid, 'parent': '1',
            'source': src, 'target': tgt, 'value': label,
            'style': "edgeStyle=orthogonalEdgeStyle;rounded=1;"
                     "strokeColor=#333333;strokeWidth=1.5;"
                     "fontSize=9;fontFamily=Helvetica;fontColor=#666666;html=1;"
                     f"endArrow=blockThin;endFill=1;{extra}",
        }
        if label_x is not None:
            cell['label_x'] = label_x
        if label_y is not None:
            cell['label_y'] = label_y
        if waypoints:
            cell['waypoints'] = waypoints
        self.d.cells.append(cell)
        return cid

    def msg_flow(self, src, tgt, label="", exit_xy=None, entry_xy=None,
                 waypoints=None):
        cid = self.d._next_id()
        extra = ""
        if exit_xy:
            extra += f"exitX={exit_xy[0]};exitY={exit_xy[1]};exitDx=0;exitDy=0;"
        if entry_xy:
            extra += f"entryX={entry_xy[0]};entryY={entry_xy[1]};entryDx=0;entryDy=0;"
        cell = {
            'type': 'edge', 'id': cid, 'parent': '1',
            'source': src, 'target': tgt, 'value': label,
            'style': "edgeStyle=orthogonalEdgeStyle;rounded=1;"
                     "strokeColor=#999999;strokeWidth=1;"
                     "fontSize=8;fontFamily=Helvetica;fontColor=#999999;html=1;"
                     f"dashed=1;dashPattern=8 4;endArrow=open;endFill=0;{extra}",
        }
        if waypoints:
            cell['waypoints'] = waypoints
        self.d.cells.append(cell)
        return cid

    def save(self, filename):
        fpath = os.path.join(OUT_DIR, filename)
        self.d.save(fpath)
        return filename


def _lbl(text, color='#666666'):
    return f"<span style='font-size:8px;color:{color}'>{text}</span>"


# ============================================================
# Helper: place gateway label safely offset from diamond
# ============================================================
def _gw_label(bp, lane, x_off, text, color, direction):
    """Place a gateway label with proper offset so it doesn't overlap.
    direction: 'right', 'bottom', 'top', 'left'
    """
    gx, gy = bp._pos(lane, x_off)
    if direction == 'right':
        bp.label_at(gx + GW_SZ + 8, gy - GW_SZ // 2 - 4, text, color)
    elif direction == 'bottom':
        bp.label_at(gx - 10, gy + GW_SZ // 2 + 6, text, color)
    elif direction == 'top':
        bp.label_at(gx - 10, gy - GW_SZ // 2 - 18, text, color)
    elif direction == 'left':
        bp.label_at(gx - 65, gy - GW_SZ // 2 - 4, text, color)


# ============================================================
# BPMN v2-01: Birth Registration Process
# ============================================================
def bpmn_v2_01_birth_registration():
    L1, L2, L3, L4, L5 = "Parent /\nGuardian", "Hospital /\nClinic", "Registration\nOfficer", "CR System", "AFIS / DAS"

    bp = BPMNDiagram(
        "Birth Registration Process",
        "DHA Lesotho - BPMN 2.0 | Civil Registration &amp; Vital Events",
        width=1500,
        lane_defs=[(L1, "citizen"), (L2, "external"), (L3, "officer"),
                   (L4, "system"), (L5, "database")]
    )

    s = bp.start(L1, 0)
    t1 = bp.user_task(L1, 80, "<b>Gather Documents</b><br><span style='font-size:8px'>Hospital record, witness ID</span>", 170)
    t2 = bp.user_task(L1, 470, "<b>Present at</b><br><b>Registration Office</b>", 175)
    t3 = bp.user_task(L1, 1050, "<b>Receive Birth</b><br><b>Certificate</b>", 160)

    t4 = bp.manual_task(L2, 80, "<b>Issue Birth</b><br><b>Notification</b>", 160)

    t5 = bp.user_task(L3, 310, "<b>Verify Documents</b>", 160)
    g1 = bp.xor(L3, 520)
    t6 = bp.user_task(L3, 610, "<b>Enter Data</b><br><b>in CR System</b>", 160)
    t7 = bp.user_task(L3, 850, "<b>Issue Birth</b><br><b>Certificate</b>", 160)

    t8 = bp.service_task(L4, 610, "<b>Store Record</b><br><b>in CR Database</b>", 170)
    t9 = bp.service_task(L4, 850, "<b>Generate</b><br><b>Certificate #</b>", 160)

    t10 = bp.service_task(L5, 610, "<b>Scan &amp; Archive</b><br><b>Documents (DAS)</b>", 170)
    e = bp.end(L5, 1050)

    bp.flow(s, t1)
    bp.flow(t1, t2)
    bp.msg_flow(t4, t5, exit_xy=(1, 0.5), entry_xy=(0, 0.5))
    bp.msg_flow(t2, t5, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t5, g1)
    bp.flow(g1, t6)
    _gw_label(bp, L3, 520, "Valid", "#2E7D32", "right")
    bp.msg_flow(g1, t1, _lbl("Incomplete", "#C62828"),
                exit_xy=(0, 0.5), entry_xy=(0.5, 1))
    bp.flow(t6, t7)
    bp.msg_flow(t6, t8, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.msg_flow(t6, t10, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t8, t9)
    bp.flow(t7, t3)
    bp.flow(t9, e)

    bp.annotation(1260, 70, "<span style='font-size:8px'><b>Volumes:</b><br>"
                  "800K certificates/yr<br>10 districts + 18 centres</span>", 180, 50)

    return bp.save("BPMN_v2_01_birth_registration.drawio")


# ============================================================
# BPMN v2-02: ePassport Issuance Process
# ============================================================
def bpmn_v2_02_epassport_issuance():
    L1, L2, L3, L4, L5 = "Applicant", "Enrollment\nStation", "AFIS / CRS", "Main Site\n(SDIS)", "Delivery\n(POA)"

    bp = BPMNDiagram(
        "ePassport Issuance Process",
        "DHA Lesotho - BPMN 2.0 | SDIS 11-Stage Lifecycle (GET Group / Toppan E2000)",
        width=2000,
        lane_defs=[(L1, "citizen"), (L2, "officer"), (L3, "system"),
                   (L4, "database"), (L5, "external")]
    )

    s = bp.start(L1, 0)
    t_apply = bp.user_task(L1, 80, "<b>Submit Passport</b><br><b>Application</b><br><span style='font-size:8px'>NID + docs + fee</span>", 170)
    t_recv = bp.user_task(L1, 1650, "<b>Collect ePassport</b><br><span style='font-size:8px'>FP verification</span>", 170)

    t_reg = bp.user_task(L2, 80, "<b>1. Register &amp;</b><br><b>Verify CRS Data</b>", 175)
    t_bio = bp.user_task(L2, 310, "<b>2. Capture</b><br><b>Biometrics</b>", 170)
    t_pay = bp.user_task(L2, 620, "<b>3. Cashier &amp;</b><br><b>Data Entry</b>", 170)
    t_aud = bp.user_task(L2, 850, "<b>4. Audit &amp;</b><br><b>Transfer</b>", 165)

    t_crs = bp.service_task(L3, 80, "<b>CRS Database</b><br><b>Lookup</b>", 170)
    t_afis = bp.service_task(L3, 310, "<b>AFIS 1:N</b><br><b>De-duplication</b>", 175)
    g1 = bp.xor(L3, 540)
    t_dup = bp.service_task(L3, 640, "<b>Duplicate Alert</b><br><span style='font-size:8px;color:#C62828'>Blocked</span>", 160)
    e_err = bp.end_error(L3, 860)

    t_val = bp.service_task(L4, 850, "<b>5. Validation</b><br><span style='font-size:8px'>Stop List check</span>", 165)
    g2 = bp.xor(L4, 1070)
    t_print = bp.service_task(L4, 1180, "<b>6. Print &amp;</b><br><b>Encode Chip</b>", 170)
    t_qa = bp.service_task(L4, 1410, "<b>7. QA Verify</b><br><span style='font-size:8px'>MRZ + Chip + UV/IR</span>", 170)
    g3 = bp.xor(L4, 1630)

    t_disp = bp.manual_task(L5, 1180, "<b>8. Dispatch</b><br><span style='font-size:8px'>POA FP auth</span>", 160)
    t_deliv = bp.manual_task(L5, 1410, "<b>9. Deliver to</b><br><b>Enrollment Site</b>", 175)
    e = bp.end(L5, 1720)

    bp.flow(s, t_apply)
    bp.msg_flow(t_apply, t_reg, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.msg_flow(t_reg, t_crs, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t_reg, t_bio)
    bp.msg_flow(t_bio, t_afis, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t_afis, g1)
    bp.flow(g1, t_dup, exit_xy=(1, 0.5), entry_xy=(0, 0.5))
    _gw_label(bp, L3, 540, "Duplicate", "#C62828", "right")
    _gw_label(bp, L3, 540, "Unique", "#2E7D32", "bottom")
    bp.flow(t_dup, e_err)
    bp.flow(g1, t_pay, exit_xy=(0.5, 0), entry_xy=(0.5, 1))
    bp.flow(t_pay, t_aud)
    bp.msg_flow(t_aud, t_val, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t_val, g2)
    _gw_label(bp, L4, 1070, "Valid", "#2E7D32", "right")
    bp.flow(g2, t_print, exit_xy=(1, 0.5), entry_xy=(0, 0.5))
    bp.flow(t_print, t_qa)
    bp.flow(t_qa, g3)
    _gw_label(bp, L4, 1630, "Pass", "#2E7D32", "right")
    bp.flow(g3, t_disp, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.msg_flow(t_disp, t_deliv)
    bp.flow(t_deliv, e)
    bp.msg_flow(t_deliv, t_recv, exit_xy=(0.5, 0), entry_xy=(0.5, 1))

    bp.annotation(1840, 70, "<span style='font-size:8px'><b>Key Details:</b><br>"
                  "300K passports/yr<br>10 enrollment stations<br>"
                  "Toppan E2000 (~50s/book)<br>ECCD chip encoding<br>"
                  "ICAO/BAC compliant</span>", 150, 80)

    return bp.save("BPMN_v2_02_epassport_issuance.drawio")


# ============================================================
# BPMN v2-03: Border Control Entry Process
# ============================================================
def bpmn_v2_03_border_control():
    L1, L2, L3, L4, L5 = "Traveller", "Border\nOfficer", "eBCS /\nMIDAS", "Alert\nDatabases", "Senior\nOfficer"

    bp = BPMNDiagram(
        "Border Control Entry Process",
        "DHA Lesotho - BPMN 2.0 | eBCS 5-Criteria Validation at BCP",
        width=1800,
        lane_defs=[(L1, "citizen"), (L2, "officer"), (L3, "system"),
                   (L4, "external"), (L5, "officer")]
    )

    s = bp.start(L1, 0)
    t1 = bp.user_task(L1, 80, "<b>Present Travel</b><br><b>Document</b>", 160)
    t_bio = bp.user_task(L1, 460, "<b>Biometric Capture</b><br><span style='font-size:8px'>Photo + Fingerprint</span>", 175)
    t_clear = bp.user_task(L1, 1370, "<b>Proceed</b><br><span style='font-size:8px'>Entry granted</span>", 150)

    t2 = bp.user_task(L2, 80, "<b>Scan MRTD</b><br><span style='font-size:8px'>Page Reader (MRZ)</span>", 165)
    t3 = bp.user_task(L2, 300, "<b>Document Auth</b><br><span style='font-size:8px'>IR + UV + White Light</span>", 170)
    t4 = bp.user_task(L2, 700, "<b>Record Visa &amp;</b><br><b>Vehicle Data</b>", 170)

    t5 = bp.service_task(L3, 300, "<b>1. MRZ &amp; Chip</b><br><b>Verification</b>", 170)
    t_io = bp.service_task(L3, 530, "<b>2. In/Out</b><br><b>Status Check</b>", 160)
    t6 = bp.service_task(L3, 700, "<b>3. Validation</b><br><b>Rules</b>", 165)
    t_fp = bp.service_task(L3, 930, "<b>5. Fingerprint</b><br><b>Match (SDIS)</b>", 170)
    g1 = bp.xor(L3, 1160)
    t_rec = bp.service_task(L3, 1280, "<b>Record</b><br><b>Entry/Exit</b>", 150)
    e = bp.end(L3, 1500)

    t8 = bp.service_task(L4, 700, "<b>4a. National</b><br><b>Alert List</b>", 160)
    t9 = bp.service_task(L4, 930, "<b>4b. INTERPOL</b><br><b>SLTD + Wanted</b>", 175)

    t_sec = bp.user_task(L5, 1160, "<b>Secondary</b><br><b>Inspection</b><br><span style='font-size:8px;color:#C62828'>Detained for review</span>", 175)
    g_force = bp.xor(L5, 1400)
    e_sec = bp.end_terminate(L5, 1520)

    bp.flow(s, t1)
    bp.msg_flow(t1, t2, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t2, t3)
    bp.msg_flow(t3, t5, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t1, t_bio)
    bp.flow(t5, t_io)
    bp.flow(t_io, t6)
    bp.flow(t3, t4)
    # Biometric to FP match - route right side to avoid L2 shapes
    bio_right = bp._pos(L1, 460)[0] + 175 + 20
    bp.msg_flow(t_bio, t_fp, exit_xy=(1, 0.5), entry_xy=(0.5, 0),
                waypoints=[(bio_right, bp._lane_cy(L1)),
                           (bio_right, bp.lane_y[L3] + 10)])
    bp.msg_flow(t6, t8, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.msg_flow(t8, t9)
    bp.flow(t6, t_fp)
    bp.flow(t_fp, g1)

    bp.flow(g1, t_sec, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(g1, t_rec, exit_xy=(1, 0.5), entry_xy=(0, 0.5))
    _gw_label(bp, L3, 1160, "Clear", "#2E7D32", "right")
    _gw_label(bp, L3, 1160, "Alert!", "#C62828", "bottom")

    bp.flow(t_sec, g_force)
    bp.flow(g_force, e_sec, _lbl("Denied"))
    # Forced accept routes up
    bp.flow(g_force, t_rec, _lbl("Forced Accept"),
            exit_xy=(0.5, 0), entry_xy=(1, 0.5))
    bp.flow(t_rec, e)
    bp.msg_flow(t_rec, t_clear, exit_xy=(0.5, 0), entry_xy=(0.5, 1))

    bp.annotation(1580, 70, "<span style='font-size:8px'><b>5 Validation Criteria:</b><br>"
                  "1. MRZ &amp; Chip data<br>2. In/Out status<br>"
                  "3. Forbidden/Quarantine<br>4. Stop List + INTERPOL<br>"
                  "5. FP match (citizens)<br><b>9 land + 1 air BCP</b></span>", 185, 90)

    return bp.save("BPMN_v2_03_border_control.drawio")


# ============================================================
# BPMN v2-04: NID Card Issuance Process
# ============================================================
def bpmn_v2_04_nid_card_issuance():
    L1, L2, L3, L4, L5 = "Applicant", "Registration\nOfficer", "AFIS /\nCR System", "Processing", "QA &amp;\nCollection"

    bp = BPMNDiagram(
        "NID Card Issuance Process",
        "DHA Lesotho - BPMN 2.0 | Civil Registration ID Card System (Nikuv / NIP Global)",
        width=1900,
        lane_defs=[(L1, "citizen"), (L2, "officer"), (L3, "system"),
                   (L4, "officer"), (L5, "database")]
    )

    s = bp.start(L1, 0)
    t_app = bp.user_task(L1, 80, "<b>Submit Application</b><br><span style='font-size:8px'>Form + docs + fees</span>", 175)
    t_img = bp.user_task(L1, 560, "<b>Provide Photo &amp;</b><br><b>Signature</b>", 175)
    t_collect = bp.user_task(L1, 1500, "<b>Collect ID Card</b><br><span style='font-size:8px'>Bearer or proxy</span>", 165)

    t_reg = bp.user_task(L2, 80, "<b>1. Register</b><br><span style='font-size:8px'>Barcode scan, CRS lookup</span>", 180)
    t_fp = bp.user_task(L2, 330, "<b>Capture 10</b><br><b>Fingerprints</b>", 165)

    t_crs = bp.service_task(L3, 80, "<b>CRS Database</b><br><b>Lookup</b>", 170)
    t_afis = bp.service_task(L3, 330, "<b>AFIS 1:N</b><br><b>Comparison</b>", 170)
    g1 = bp.xor(L3, 560)
    t_susp = bp.service_task(L3, 670, "<b>Auto-Suspend</b><br><span style='font-size:8px;color:#C62828'>FP match found</span>", 165)

    t_de = bp.user_task(L4, 330, "<b>2. Data Entry</b><br><span style='font-size:8px'>Full details + doc scan</span>", 175)
    t_ver = bp.user_task(L4, 570, "<b>3. Verification &amp;</b><br><b>Corrections</b>", 175)
    t_supv = bp.user_task(L4, 810, "<b>4. Supervisor</b><br><b>Review</b>", 170)
    g2 = bp.xor(L4, 1040)
    e_rej = bp.end_error(L4, 1150)
    t_print = bp.user_task(L4, 1230, "<b>5. Print ID Card</b><br><span style='font-size:8px'>Secure stock + serial #</span>", 180)

    t_qa = bp.service_task(L5, 1230, "<b>6. QA Check</b><br><span style='font-size:8px'>Serial, MRZ, 2D Barcode</span>", 180)
    g3 = bp.xor(L5, 1470)
    t_coll = bp.user_task(L5, 1570, "<b>7. Collection</b><br><span style='font-size:8px'>ID verify + handover</span>", 170)
    e = bp.end(L5, 1790)

    bp.flow(s, t_app)
    bp.flow(t_app, t_img)
    bp.msg_flow(t_app, t_reg, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.msg_flow(t_reg, t_crs, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t_reg, t_fp)
    bp.msg_flow(t_fp, t_afis, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t_afis, g1)

    _gw_label(bp, L3, 560, "Match!", "#C62828", "right")
    _gw_label(bp, L3, 560, "Unique", "#2E7D32", "bottom")
    bp.flow(g1, t_susp, exit_xy=(1, 0.5), entry_xy=(0, 0.5))
    bp.msg_flow(t_susp, t_supv, exit_xy=(0.5, 1), entry_xy=(0.5, 0))

    bp.flow(g1, t_de, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t_de, t_ver)
    bp.flow(t_ver, t_supv)
    bp.flow(t_supv, g2)

    _gw_label(bp, L4, 1040, "Rejected", "#C62828", "right")
    _gw_label(bp, L4, 1040, "Approved", "#2E7D32", "bottom")
    bp.flow(g2, e_rej, exit_xy=(1, 0.5), entry_xy=(0, 0.5))
    bp.flow(g2, t_print, exit_xy=(0.5, 1), entry_xy=(0.5, 0),
            waypoints=[(bp._pos(L4, 1040)[0] + GW_SZ // 2, bp._lane_cy(L4) + LANE_H // 2 - 15),
                       (bp._pos(L4, 1230)[0] + 90, bp._lane_cy(L4) + LANE_H // 2 - 15)])

    bp.msg_flow(t_print, t_qa, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t_qa, g3)

    _gw_label(bp, L5, 1470, "Pass", "#2E7D32", "right")
    bp.flow(g3, t_coll, exit_xy=(1, 0.5), entry_xy=(0, 0.5))
    bp.flow(t_coll, e)
    bp.msg_flow(t_coll, t_collect, exit_xy=(0.5, 0), entry_xy=(0.5, 1))

    bp.annotation(1700, 70, "<span style='font-size:8px'><b>Key Details:</b><br>"
                  "600K ID cards/yr<br>8-step workflow<br>"
                  "Nikuv / NIP Global<br>AFIS dedup + Stop List<br>"
                  "Mobile Kit for remote</span>", 170, 75)

    return bp.save("BPMN_v2_04_nid_card_issuance.drawio")


# ============================================================
# BPMN v2-05: Biometric Enrollment & De-duplication
# ============================================================
def bpmn_v2_05_biometric_enrollment():
    L1, L2, L3, L4, L5 = "Applicant", "Registration\nOfficer", "AFIS\n(Biometric)", "CR / Passport\nDatabase", "DAS\n(Archiving)"

    bp = BPMNDiagram(
        "Biometric Enrollment &amp; De-duplication",
        "DHA Lesotho - BPMN 2.0 | Identity Registration with AFIS Verification",
        width=1700,
        lane_defs=[(L1, "citizen"), (L2, "officer"), (L3, "system"),
                   (L4, "database"), (L5, "system")]
    )

    s = bp.start(L1, 0)
    t1 = bp.user_task(L1, 80, "<b>Submit Application</b><br><span style='font-size:8px'>Form + supporting docs</span>", 175)
    t_bio = bp.user_task(L1, 340, "<b>Provide Biometrics</b><br><span style='font-size:8px'>Photo, 10 prints, signature</span>", 185)
    t_cred = bp.user_task(L1, 1300, "<b>Receive Credential</b><br><span style='font-size:8px'>ID / Passport / Cert</span>", 175)

    t2 = bp.user_task(L2, 80, "<b>Verify Documents</b>", 170)
    t3 = bp.user_task(L2, 340, "<b>Capture</b><br><b>Biometric Data</b>", 175)
    t4 = bp.user_task(L2, 1100, "<b>Approve &amp; Issue</b><br><b>Credential</b>", 175)

    t5 = bp.service_task(L3, 590, "<b>Demographic</b><br><b>De-duplication</b>", 180)
    t6 = bp.service_task(L3, 830, "<b>Biometric 1:N</b><br><b>Matching</b>", 180)
    g1 = bp.xor(L3, 1070)
    t_alert = bp.service_task(L3, 1180, "<b>Duplicate Alert</b><br><span style='font-size:8px;color:#C62828'>Blocked</span>", 165)
    e_err = bp.end_error(L3, 1400)

    t7 = bp.service_task(L4, 1100, "<b>Generate</b><br><b>Unique ID</b>", 165)
    t8 = bp.service_task(L4, 1330, "<b>Store Record</b><br><b>in Central DB</b>", 175)
    e = bp.end(L4, 1560)

    t9 = bp.service_task(L5, 340, "<b>Scan &amp; Archive</b><br><b>All Documents</b>", 175)

    bp.flow(s, t1)
    bp.msg_flow(t1, t2, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t1, t_bio)
    bp.flow(t2, t3)
    bp.msg_flow(t3, t5, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.msg_flow(t3, t9, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t5, t6)
    bp.flow(t6, g1)
    bp.flow(g1, t_alert, exit_xy=(1, 0.5), entry_xy=(0, 0.5))
    bp.flow(t_alert, e_err)
    bp.flow(g1, t7, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    _gw_label(bp, L3, 1070, "Duplicate", "#C62828", "right")
    _gw_label(bp, L3, 1070, "Unique", "#2E7D32", "bottom")
    bp.flow(t7, t4, exit_xy=(0.5, 0), entry_xy=(0.5, 1))
    bp.flow(t7, t8)
    bp.flow(t4, t_cred)
    bp.flow(t8, e)

    bp.annotation(1500, 70, "<span style='font-size:8px'><b>Annual Volumes:</b><br>"
                  "600K ID cards<br>300K passports<br>"
                  "800K certificates<br>10 stations</span>", 165, 60)

    return bp.save("BPMN_v2_05_biometric_enrollment.drawio")


# ============================================================
# BPMN v2-06: Identity Verification (NID Authentication)
# ============================================================
def bpmn_v2_06_identity_verification():
    L1, L2, L3, L4 = "Citizen", "Relying Party\n(Bank/Gov/MNO)", "NID System\n(ABIS)", "Identity\nDatabase"

    bp = BPMNDiagram(
        "Identity Verification Process",
        "DHA Lesotho - BPMN 2.0 | NID Authentication for Relying Parties",
        width=1700,
        lane_defs=[(L1, "citizen"), (L2, "external"), (L3, "system"),
                   (L4, "database")]
    )

    s = bp.start(L1, 0)
    t1 = bp.user_task(L1, 80, "<b>Request Service</b><br><span style='font-size:8px'>Bank, SIM, pension</span>", 175)
    t2 = bp.user_task(L1, 460, "<b>Present ID Card</b><br><b>or Biometric</b>", 170)
    t_deny = bp.manual_task(L1, 1330, "<b>Access Denied</b>", 140)

    t3 = bp.user_task(L2, 80, "<b>Initiate ID</b><br><b>Verification</b>", 170)
    t4 = bp.user_task(L2, 310, "<b>Capture Citizen</b><br><b>Credentials</b>", 175)
    t8 = bp.user_task(L2, 820, "<b>Process</b><br><b>Verification Result</b>", 185)
    g2 = bp.xor(L2, 1070)
    t_grant = bp.user_task(L2, 1180, "<b>Grant Access &amp;</b><br><b>Deliver Service</b>", 185)
    e = bp.end(L2, 1440)

    t5 = bp.service_task(L3, 460, "<b>Receive</b><br><b>Auth Request</b>", 170)
    t6 = bp.service_task(L3, 680, "<b>Verify Identity</b><br><span style='font-size:8px'>Biometric or Demographic</span>", 180)
    t7 = bp.service_task(L3, 920, "<b>Return Yes / No</b>", 160)

    t_db = bp.service_task(L4, 680, "<b>Query Identity</b><br><b>Records &amp; Templates</b>", 190)
    t_log = bp.service_task(L4, 940, "<b>Log Auth Request</b><br><span style='font-size:8px'>Audit trail</span>", 170)
    e2 = bp.end(L4, 1170)

    bp.flow(s, t1)
    bp.msg_flow(t1, t3, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t3, t4)
    bp.msg_flow(t4, t2, exit_xy=(0.5, 0), entry_xy=(0.5, 1))
    bp.msg_flow(t2, t5, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t5, t6)
    bp.msg_flow(t6, t_db, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t6, t7)
    bp.msg_flow(t7, t8, exit_xy=(0.5, 0), entry_xy=(0.5, 1))
    bp.flow(t7, t_log)
    bp.flow(t8, g2)
    _gw_label(bp, L2, 1070, "Yes", "#2E7D32", "right")
    _gw_label(bp, L2, 1070, "No", "#C62828", "top")
    bp.flow(g2, t_grant)
    bp.flow(g2, t_deny, exit_xy=(0.5, 0), entry_xy=(0.5, 1))
    bp.flow(t_grant, e)
    bp.flow(t_log, e2)

    bp.annotation(1490, 70, "<span style='font-size:8px'><b>Relying Parties:</b><br>"
                  "Banks (eKYC), Insurance,<br>MNOs (SIM reg), HRMIS,<br>"
                  "Social Programs, Health<br><b>Future:</b> Remote biometric<br>"
                  "auth for onboarding</span>", 185, 75)

    return bp.save("BPMN_v2_06_identity_verification.drawio")


# ============================================================
# BPMN v2-07: eServices Digital Service Delivery
# ============================================================
def bpmn_v2_07_eservices():
    L1, L2, L3, L4, L5 = "Citizen", "eServices\nPortal", "NID\nAuthentication", "Ministry\nBackend", "Payment\nGateway"

    bp = BPMNDiagram(
        "eServices Digital Service Delivery",
        "DHA Lesotho - BPMN 2.0 | Citizen-Centric Government Service Flow (Planned)",
        width=1800,
        lane_defs=[(L1, "citizen"), (L2, "system"), (L3, "database"),
                   (L4, "officer"), (L5, "external")]
    )

    s = bp.start(L1, 0)
    t1 = bp.user_task(L1, 80, "<b>Access Portal</b><br><span style='font-size:8px'>Web / Mobile / e-Centre</span>", 170)
    t2 = bp.user_task(L1, 490, "<b>Select Service</b><br><span style='font-size:8px'>202 services, 17 ministries</span>", 180)
    t3 = bp.user_task(L1, 730, "<b>Submit Request</b><br><span style='font-size:8px'>Pre-filled from NID</span>", 175)
    t_recv = bp.user_task(L1, 1340, "<b>Receive Service</b><br><b>&amp; Feedback</b>", 170)

    t4 = bp.service_task(L2, 80, "<b>Load Service</b><br><b>Catalog</b>", 165)
    t5 = bp.service_task(L2, 300, "<b>Request</b><br><b>Authentication</b>", 170)
    g1 = bp.xor(L2, 770)
    t6 = bp.service_task(L2, 880, "<b>Route to</b><br><b>Ministry System</b>", 175)
    t7 = bp.service_task(L2, 1240, "<b>Notify Citizen</b><br><span style='font-size:8px'>SMS / Email</span>", 165)
    e = bp.end(L2, 1470)

    t8 = bp.service_task(L3, 300, "<b>Verify Identity</b><br><span style='font-size:8px'>NID + PIN or Biometric</span>", 180)
    g_auth = bp.xor(L3, 540)
    t_deny = bp.service_task(L3, 660, "<b>Access Denied</b>", 150)
    e_deny = bp.end_error(L3, 870)

    t9 = bp.service_task(L4, 880, "<b>Process Service</b><br><b>Request</b>", 175)
    t10 = bp.service_task(L4, 1110, "<b>Prepare</b><br><b>Deliverable</b>", 170)

    t11 = bp.service_task(L5, 880, "<b>Process Payment</b><br><span style='font-size:8px'>National Payment Switch</span>", 185)
    g_pay = bp.xor(L5, 1120)

    bp.flow(s, t1)
    bp.msg_flow(t1, t4, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t4, t5)
    bp.msg_flow(t5, t8, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    bp.flow(t8, g_auth)
    bp.flow(g_auth, t_deny, exit_xy=(1, 0.5), entry_xy=(0, 0.5))
    bp.flow(t_deny, e_deny)
    bp.flow(g_auth, g1, exit_xy=(0.5, 0), entry_xy=(0.5, 1))
    _gw_label(bp, L3, 540, "Failed", "#C62828", "right")
    _gw_label(bp, L3, 540, "OK", "#2E7D32", "top")
    bp.flow(t1, t2)
    bp.flow(t2, t3)
    bp.flow(g1, t6)
    bp.msg_flow(t6, t9, exit_xy=(0.5, 1), entry_xy=(0.5, 0))
    # Submit -> Payment: route right of Submit box, then down
    submit_right = bp._pos(L1, 730)[0] + 175 + 25
    bp.msg_flow(t3, t11, exit_xy=(1, 0.5), entry_xy=(0.5, 0),
                waypoints=[(submit_right, bp._lane_cy(L1)),
                           (submit_right, bp.lane_y[L5] + 10)])
    bp.flow(t11, g_pay)
    bp.flow(t9, t10)
    bp.flow(t10, t7, exit_xy=(0.5, 0), entry_xy=(0.5, 1))
    bp.flow(t7, e)
    bp.msg_flow(t7, t_recv, exit_xy=(0.5, 0), entry_xy=(0.5, 1))

    bp.annotation(1590, 70, "<span style='font-size:8px'><b>Targets (NDTS):</b><br>"
                  "2025: 15% digitalized<br>2026: 50% digitalized<br>"
                  "2027: 70% digitalized<br>20 e-Centres, 5 ID services</span>", 180, 65)

    return bp.save("BPMN_v2_07_eservices.drawio")


# ============================================================
# Export & Main
# ============================================================
def export_png(drawio_file):
    png_file = drawio_file.replace('.drawio', '.png')
    in_path = os.path.join(OUT_DIR, drawio_file)
    out_path = os.path.join(OUT_DIR, png_file)
    subprocess.run([
        DRAWIO_EXE, '--export', '--format', 'png',
        '--scale', '2', '--output', out_path, in_path
    ], check=True)
    print(f"    Exported: {png_file}")


def main():
    print("=" * 60)
    print("Creating 7 BPMN Process Diagrams v2 for DHA Lesotho")
    print("  Using native draw.io BPMN shapes (bpmn.task/event/gateway2)")
    print("=" * 60)

    diagrams = [
        ("BPMN v2-01: Birth Registration", bpmn_v2_01_birth_registration),
        ("BPMN v2-02: ePassport Issuance", bpmn_v2_02_epassport_issuance),
        ("BPMN v2-03: Border Control Entry", bpmn_v2_03_border_control),
        ("BPMN v2-04: NID Card Issuance", bpmn_v2_04_nid_card_issuance),
        ("BPMN v2-05: Biometric Enrollment", bpmn_v2_05_biometric_enrollment),
        ("BPMN v2-06: Identity Verification", bpmn_v2_06_identity_verification),
        ("BPMN v2-07: eServices Delivery", bpmn_v2_07_eservices),
    ]

    for name, fn in diagrams:
        print(f"\n  {name}...")
        fname = fn()
        print(f"    Created: {fname}")
        export_png(fname)

    print("\n" + "=" * 60)
    print("Done! All 7 BPMN v2 diagrams created.")
    print("=" * 60)


if __name__ == '__main__':
    main()
