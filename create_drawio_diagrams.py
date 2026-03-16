"""
Draw.io diagram generation framework with DrawioBuilder class.

Three shape systems:
1. Built-in shapes: box, diamond, cylinder, hexagon, cloud, group
2. Native mxgraph references: native() - shape=mxgraph.ns.name (small XML, sidebar-identical)
3. Stencil embedding: stencil() - shape=stencil(b64) (fallback for unsupported namespaces)

DrawioBuilder provides: box, diamond, cylinder, hexagon, cloud, group, native,
stencil, connect, connect_lr, title, subtitle, header, save.

Currently includes 10 architecture diagrams for the LESICT01 project.
The DrawioBuilder class is reusable for any draw.io diagram generation.
"""
import os
import subprocess
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

# ============================================================
# Paths
# ============================================================
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(WORK_DIR, 'diagrams_drawio')
os.makedirs(OUT_DIR, exist_ok=True)

DRAWIO_EXE = os.path.join(
    os.environ.get('LOCALAPPDATA', ''),
    r'Microsoft\WinGet\Packages\JGraph.Draw_Microsoft.Winget.Source_8wekyb3d8bbwe\DrawIO.exe'
)

# ============================================================
# Color Palette
# ============================================================
C = {
    'green':      {'fill': '#C8E6C9', 'stroke': '#2E7D32', 'font': '#1B5E20'},
    'blue':       {'fill': '#E3F2FD', 'stroke': '#1565C0', 'font': '#0D47A1'},
    'red':        {'fill': '#FFCCCC', 'stroke': '#CC0000', 'font': '#8B0000'},
    'yellow':     {'fill': '#FFF9C4', 'stroke': '#F9A825', 'font': '#F57F17'},
    'orange':     {'fill': '#FFF3E0', 'stroke': '#E65100', 'font': '#BF360C'},
    'purple':     {'fill': '#E1BEE7', 'stroke': '#7B1FA2', 'font': '#4A148C'},
    'gray':       {'fill': '#F5F5F5', 'stroke': '#9E9E9E', 'font': '#424242'},
    'dark_blue':  {'fill': '#1565C0', 'stroke': '#0D47A1', 'font': '#FFFFFF'},
    'dark_green': {'fill': '#2E7D32', 'stroke': '#1B5E20', 'font': '#FFFFFF'},
    'dark_red':   {'fill': '#CC0000', 'stroke': '#8B0000', 'font': '#FFFFFF'},
    'white':      {'fill': '#FFFFFF', 'stroke': '#333333', 'font': '#333333'},
    'teal':       {'fill': '#E0F2F1', 'stroke': '#00695C', 'font': '#004D40'},
    'light_gray': {'fill': '#FAFAFA', 'stroke': '#BDBDBD', 'font': '#616161'},
    'none':       {'fill': 'none', 'stroke': 'none', 'font': '#333333'},
}

# ============================================================
# XML Builder
# ============================================================
class DrawioBuilder:
    """Builds a .drawio XML file with proper styling."""

    def __init__(self, page_name="Page", page_w=1100, page_h=850):
        self._id_counter = 2
        self.cells = []
        self.page_name = page_name
        self.page_w = page_w
        self.page_h = page_h

    def _next_id(self):
        self._id_counter += 1
        return str(self._id_counter)

    def _style_str(self, colors, extra=None):
        parts = [
            f"fillColor={colors['fill']}",
            f"strokeColor={colors['stroke']}",
            f"fontColor={colors['font']}",
            "rounded=1", "whiteSpace=wrap", "html=1",
            "fontSize=11", "fontFamily=Helvetica",
        ]
        if extra:
            if isinstance(extra, list):
                parts.extend(extra)
            else:
                parts.append(extra)
        return ";".join(parts) + ";"

    def box(self, label, x, y, w, h, colors, extra=None, parent="1"):
        cid = self._next_id()
        self.cells.append({
            'type': 'vertex', 'id': cid, 'parent': parent,
            'value': label,
            'style': self._style_str(colors, extra),
            'x': x, 'y': y, 'w': w, 'h': h,
        })
        return cid

    def group(self, label, x, y, w, h, colors, extra=None):
        extras = [
            "fontSize=13", "fontStyle=1", "verticalAlign=top",
            "dashed=1", "dashPattern=8 4", "opacity=50", "strokeWidth=2",
        ]
        if extra:
            extras.extend(extra if isinstance(extra, list) else [extra])
        return self.box(label, x, y, w, h, colors, extras)

    def header(self, label, x, y, w, h, colors):
        return self.box(label, x, y, w, h, colors, ["fontStyle=1", "shadow=1"])

    def title(self, label, x, y, w=700, h=40):
        cid = self._next_id()
        self.cells.append({
            'type': 'vertex', 'id': cid, 'parent': '1',
            'value': label,
            'style': "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;"
                     "fontSize=16;fontFamily=Helvetica;fontStyle=1;fillColor=none;"
                     "strokeColor=none;fontColor=#333333;",
            'x': x, 'y': y, 'w': w, 'h': h,
        })
        return cid

    def subtitle(self, label, x, y, w=700, h=25):
        cid = self._next_id()
        self.cells.append({
            'type': 'vertex', 'id': cid, 'parent': '1',
            'value': label,
            'style': "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;"
                     "fontSize=11;fontFamily=Helvetica;fontStyle=2;fillColor=none;"
                     "strokeColor=none;fontColor=#666666;",
            'x': x, 'y': y, 'w': w, 'h': h,
        })
        return cid

    def diamond(self, label, x, y, w, h, colors):
        return self.box(label, x, y, w, h, colors,
                        ["shape=rhombus", "perimeter=rhombusPerimeter"])

    def hexagon(self, label, x, y, w, h, colors):
        return self.box(label, x, y, w, h, colors,
                        ["shape=hexagon", "perimeter=hexagonPerimeter2", "size=0.25"])

    def cylinder(self, label, x, y, w, h, colors):
        return self.box(label, x, y, w, h, colors, ["shape=cylinder3", "size=10"])

    def cloud(self, label, x, y, w, h, colors):
        return self.box(label, x, y, w, h, colors, ["shape=cloud"])

    def stencil(self, label, x, y, w, h, shape_info, colors=None, extra=None):
        """Use a draw.io stencil shape (from drawio_stencil_catalog).

        Args:
            shape_info: Either a catalog dict {"w":..,"h":..,"b64":"..."}
                        from STENCILS[ns][name], or a raw b64 string.
            colors: Optional color dict from C palette (fill/stroke for the icon).
            extra: Optional extra style parameters list.

        Example:
            from drawio_stencil_catalog import STENCILS
            d.stencil("DC Server", 100, 200, 60, 80,
                      STENCILS["mxgraph.networks"]["Server"], C['blue'])
        """
        if isinstance(shape_info, dict):
            b64 = shape_info['b64']
        else:
            b64 = shape_info
        parts = [f"shape=stencil({b64})",
                 "verticalLabelPosition=bottom", "verticalAlign=top",
                 "align=center", "html=1",
                 "fontSize=11", "fontFamily=Helvetica"]
        if colors:
            parts.extend([
                f"fillColor={colors['fill']}",
                f"strokeColor={colors['stroke']}",
                f"fontColor={colors['font']}",
            ])
        if extra:
            parts.extend(extra if isinstance(extra, list) else [extra])
        cid = self._next_id()
        self.cells.append({
            'type': 'vertex', 'id': cid, 'parent': '1',
            'value': label,
            'style': ";".join(parts) + ";",
            'x': x, 'y': y, 'w': w, 'h': h,
        })
        return cid

    def native(self, label, x, y, w, h, shape_ref, colors=None, extra=None):
        """Use a native draw.io shape reference (shape=mxgraph.ns.name).

        Produces smaller XML than stencil(b64) and renders identically to
        shapes dragged from draw.io Desktop's sidebar menu.

        Args:
            shape_ref: Native reference string, e.g. "mxgraph.networks.server",
                       "mxgraph.aws4.ec2", "mxgraph.azure.virtual_machine".
            colors: Optional color dict from C palette.
            extra: Optional extra style parameters list.

        Confirmed working namespaces (tested with CLI export):
            mxgraph.networks.*     - ALL shapes (server, switch, router, firewall, cloud, ...)
            mxgraph.aws4.*         - Most shapes (ec2, s3, lambda, rds, vpc, sqs, sns, ...)
            mxgraph.office.*       - ALL sub-namespaces (servers, users, clouds, security, ...)
            mxgraph.gcp2.*         - Most shapes (compute_engine, cloud_storage, cloud_sql, ...)
            mxgraph.cisco.*        - Most shapes (routers.router, switches.*, security.*, ...)
            mxgraph.cisco_safe.*   - ALL sub-namespaces (architecture, capability, design, ...)
            mxgraph.cisco19.*      - Most shapes (router, firewall, server, cloud, laptop, ...)
            mxgraph.azure.*        - Partial (virtual_machine, sql_database, storage, cloud, ...)
            mxgraph.basic.*        - Most shapes (star, heart, cube, cone2, banner, ...)
            mxgraph.rack.*         - Rack equipment strips
            mxgraph.bpmn.*         - Use BPMNDiagram class instead

        NOT working (use stencil() instead):
            mxGraph.flowchart.*    - Use built-in shapes (rhombus, cylinder3, document, ...)
            mxgraph.ibm_cloud.*    - Use stencil(b64)
            mxgraph.atlassian.*    - Use stencil(b64)

        Example:
            d.native("DC Server", 100, 200, 60, 80,
                     "mxgraph.networks.server", C['blue'])
        """
        parts = [f"shape={shape_ref}",
                 "outlineConnect=0", "aspect=fixed",
                 "verticalLabelPosition=bottom", "verticalAlign=top",
                 "align=center", "html=1",
                 "fontSize=11", "fontFamily=Helvetica"]
        if colors:
            parts.extend([
                f"fillColor={colors['fill']}",
                f"strokeColor={colors['stroke']}",
                f"fontColor={colors['font']}",
            ])
        if extra:
            parts.extend(extra if isinstance(extra, list) else [extra])
        cid = self._next_id()
        self.cells.append({
            'type': 'vertex', 'id': cid, 'parent': '1',
            'value': label,
            'style': ";".join(parts) + ";",
            'x': x, 'y': y, 'w': w, 'h': h,
        })
        return cid

    def connect(self, src, tgt, label="", color="#666666", dashed=False,
                exit_xy=None, entry_xy=None, waypoints=None):
        cid = self._next_id()
        # Use segmentEdgeStyle when waypoints are given for exact control
        edge_style = "edgeStyle=segmentEdgeStyle" if waypoints else "edgeStyle=orthogonalEdgeStyle"
        parts = [
            f"strokeColor={color}",
            "rounded=1", "fontSize=9", "fontFamily=Helvetica",
            "fontColor=#666666", "html=1",
            edge_style,
        ]
        if exit_xy:
            parts.append(f"exitX={exit_xy[0]};exitY={exit_xy[1]};exitDx=0;exitDy=0")
        elif not waypoints:
            parts.append("exitX=0.5;exitY=1;exitDx=0;exitDy=0")
        if entry_xy:
            parts.append(f"entryX={entry_xy[0]};entryY={entry_xy[1]};entryDx=0;entryDy=0")
        if dashed:
            parts.append("dashed=1")
        cell = {
            'type': 'edge', 'id': cid, 'parent': '1',
            'source': src, 'target': tgt,
            'value': label,
            'style': ";".join(parts) + ";",
        }
        if waypoints:
            cell['waypoints'] = waypoints
        self.cells.append(cell)
        return cid

    def connect_lr(self, src, tgt, label="", color="#666666", dashed=False,
                   exit_xy=None, entry_xy=None, waypoints=None):
        """Connect with left-right flow style."""
        cid = self._next_id()
        parts = [
            f"strokeColor={color}",
            "rounded=1", "fontSize=9", "fontFamily=Helvetica",
            "fontColor=#666666", "html=1",
            "edgeStyle=orthogonalEdgeStyle",
        ]
        if exit_xy:
            parts.append(f"exitX={exit_xy[0]};exitY={exit_xy[1]};exitDx=0;exitDy=0")
        if entry_xy:
            parts.append(f"entryX={entry_xy[0]};entryY={entry_xy[1]};entryDx=0;entryDy=0")
        if dashed:
            parts.append("dashed=1")
        cell = {
            'type': 'edge', 'id': cid, 'parent': '1',
            'source': src, 'target': tgt,
            'value': label,
            'style': ";".join(parts) + ";",
        }
        if waypoints:
            cell['waypoints'] = waypoints
        self.cells.append(cell)
        return cid

    def save(self, filepath):
        """Write the .drawio XML file."""
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<mxfile host="Claude" modified="2026-03-05" agent="LESICT01" version="21.6.5">')
        lines.append(f'  <diagram name="{escape(self.page_name)}" id="page1">')
        lines.append(f'    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" '
                     f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
                     f'page="1" pageScale="1" pageWidth="{self.page_w}" pageHeight="{self.page_h}" '
                     f'math="0" shadow="0">')
        lines.append('      <root>')
        lines.append('        <mxCell id="0"/>')
        lines.append('        <mxCell id="1" parent="0"/>')

        for cell in self.cells:
            if cell['type'] == 'vertex':
                val = escape(cell['value'])
                sty = escape(cell['style'])
                lines.append(f'        <mxCell id="{cell["id"]}" value="{val}" '
                           f'style="{sty}" vertex="1" parent="{cell["parent"]}">')
                lines.append(f'          <mxGeometry x="{cell["x"]}" y="{cell["y"]}" '
                           f'width="{cell["w"]}" height="{cell["h"]}" as="geometry"/>')
                lines.append(f'        </mxCell>')
            elif cell['type'] == 'edge':
                val = escape(cell.get('value', ''))
                sty = escape(cell['style'])
                src_attr = f' source="{cell["source"]}"' if cell.get('source') else ''
                tgt_attr = f' target="{cell["target"]}"' if cell.get('target') else ''
                lines.append(f'        <mxCell id="{cell["id"]}" value="{val}" '
                           f'style="{sty}" edge="1" parent="1"'
                           f'{src_attr}{tgt_attr}>')
                # Support label offset positioning and waypoints
                lbl_x = cell.get('label_x')
                lbl_y = cell.get('label_y')
                wps = cell.get('waypoints')
                has_inner = (lbl_x is not None or lbl_y is not None) or wps
                if has_inner:
                    lx = lbl_x if lbl_x is not None else 0
                    ly = lbl_y if lbl_y is not None else 0
                    lines.append(f'          <mxGeometry x="{lx}" y="{ly}" relative="1" as="geometry">')
                    if wps:
                        lines.append(f'            <Array as="points">')
                        for px, py in wps:
                            lines.append(f'              <mxPoint x="{px}" y="{py}"/>')
                        lines.append(f'            </Array>')
                    lines.append(f'          </mxGeometry>')
                else:
                    lines.append(f'          <mxGeometry relative="1" as="geometry"/>')
                lines.append(f'        </mxCell>')

        lines.append('      </root>')
        lines.append('    </mxGraphModel>')
        lines.append('  </diagram>')
        lines.append('</mxfile>')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


# ============================================================
# Diagram 01: IT Systems Integration Map
# LAYOUT: 3 columns - Impala(left) | GET+AFIS(center) | External(right)
# No tech specs here (those belong in D03/D05/D06)
# ============================================================
def diagram_01():
    d = DrawioBuilder("IT Systems Integration Map", 1100, 680)

    d.title("<b>IT Systems Integration Map</b>", 200, 10, 700, 35)
    d.subtitle("DHA Lesotho - Current System Landscape (March 2026)", 200, 45, 700, 25)

    # Vendor groups
    d.group("<b>Impala Technologies / NIP Global</b>", 30, 85, 430, 340, C['green'])
    d.group("<b>GET Group</b>", 510, 85, 310, 340, C['blue'])

    # Impala systems - Row 1: CR alone (clear path to SDIS)
    cr = d.box(
        "<b>CR</b><br><span style='font-size:10px'>Civil Registration</span><br>"
        "<span style='font-size:9px;color:#666'>Births, Marriages, Deaths, Divorces</span>",
        55, 130, 190, 65, C['green'], ["shadow=1"])

    # Row 2: NICR + GI side by side (GI moved down from row 1)
    nicr = d.box(
        "<b>NICR</b><br><span style='font-size:10px'>National Identity</span><br>"
        "<span style='font-size:9px;color:#666'>ID card issuance + biometrics</span>",
        55, 240, 190, 65, C['green'], ["shadow=1"])

    gi = d.box(
        "<b>GI</b><br><span style='font-size:10px'>Generic Interface</span><br>"
        "<span style='font-size:9px;color:#666'>Identity Verification API</span>",
        270, 240, 170, 55, C['green'], ["shadow=1"])

    # Row 3: Mobile
    mob = d.box(
        "<b>Mobile Registration</b><br>"
        "<span style='font-size:9px;color:#666'>2 kits, offline-capable</span>",
        270, 335, 170, 50, C['yellow'], ["shadow=1"])

    # GET systems
    sdis = d.box(
        "<b>SDIS</b><br><span style='font-size:10px'>ePassport Issuance</span>",
        535, 130, 180, 50, C['blue'], ["shadow=1"])

    ebcs = d.box(
        "<b>eBCS</b><br><span style='font-size:10px'>Border Control</span><br>"
        "<span style='font-size:9px;color:#666'>9 automated + 1 airport</span>",
        535, 215, 180, 60, C['blue'], ["shadow=1"])

    sdms = d.box(
        "<b>SDMS</b><br><span style='font-size:10px'>Document Management</span>",
        535, 310, 180, 45, C['blue'], ["shadow=1"])

    # KMS + Stop Lists - right column
    kms = d.box(
        "<b>KMS</b><br><span style='font-size:10px'>ePassport PKI</span>",
        870, 130, 130, 50, C['blue'], ["shadow=1"])

    stop = d.box(
        "<b>Stop Lists</b><br>"
        "<span style='font-size:9px;color:#666'>Individual, Doc, Vehicle</span>",
        870, 215, 130, 50, C['red'], ["shadow=1"])

    # External consumers - far right, below GET group (avoid crossing GET area)
    ext = d.box(
        "<b>External Consumers</b><br>"
        "<span style='font-size:9px;color:#666'>Banks (KYC), Telecoms</span><br>"
        "<span style='font-size:9px;color:#888'>Gov agencies</span>",
        870, 460, 130, 65, C['gray'], ["shadow=1"])

    # AFIS - centered below GET group (connects up to SDIS, left to NICR)
    afis = d.hexagon(
        "<b>AFIS</b><br><span style='font-size:9px'>Fingerprint Matching</span><br>"
        "<span style='font-size:9px;color:#CC0000'>SPOF</span>",
        560, 460, 160, 75, C['red'])

    # Other systems - bottom left (well separated from AFIS)
    lrmis = d.box(
        "<b>LRMIS</b><br><span style='font-size:10px'>Livestock Registration</span><br>"
        "<span style='font-size:9px;color:#666'>CBS - 60+ centres</span>",
        30, 470, 160, 55, C['yellow'], ["shadow=1"])

    resperm = d.box(
        "<b>ResPerm</b><br><span style='font-size:10px'>eResidence Permits</span>",
        30, 555, 160, 45, C['purple'], ["shadow=1"])

    evisa = d.box(
        "<b>eVisa</b><br><span style='font-size:9px;color:#CC0000'>INACTIVE</span>",
        210, 555, 120, 45, C['red'], ["shadow=1"])

    # Connectors - no crossing: CR alone on top row, clear path to SDIS
    d.connect(cr, nicr, "citizen data", C['green']['stroke'])
    d.connect_lr(nicr, gi, "", C['green']['stroke'])
    d.connect_lr(cr, sdis, "NID validation", "#666666")
    d.connect(sdis, ebcs, "biometric data", C['blue']['stroke'])
    d.connect(ebcs, sdms, "", C['blue']['stroke'])
    d.connect_lr(kms, sdis, "PKI", C['blue']['stroke'])
    d.connect_lr(stop, ebcs, "validation", C['red']['stroke'])
    # GI→External: goes down from GI then right to External (below GET group)
    d.connect(gi, ext, "KYC / SIM reg", "#999999")
    d.connect_lr(mob, nicr, "sync", C['green']['stroke'], dashed=True)
    # AFIS dedup - positioned under GET, connects up to SDIS and left to NICR
    d.connect(afis, nicr, "dedup", C['red']['stroke'], dashed=True)
    d.connect(afis, sdis, "dedup", C['red']['stroke'], dashed=True)

    # Legend
    d.box("<b>Active</b>", 870, 550, 60, 20, C['green'], ["fontSize=9"])
    d.box("<b>Critical</b>", 935, 550, 60, 20, C['red'], ["fontSize=9"])
    d.box("<b>Limited</b>", 870, 573, 60, 20, C['yellow'], ["fontSize=9"])
    d.box("<b>External</b>", 935, 573, 60, 20, C['gray'], ["fontSize=9"])

    fname = "01_it_systems_integration.drawio"
    d.save(os.path.join(OUT_DIR, fname))
    return fname


# ============================================================
# Diagram 02: Network Architecture
# ============================================================
def diagram_02():
    d = DrawioBuilder("Network Architecture", 1100, 850)

    d.title("<b>Network Architecture</b>", 200, 10, 700, 35)
    d.subtitle("DHA Lesotho - Central Data Centre &amp; WAN Topology", 200, 45, 700, 25)

    # DC Group
    d.group("<b>Central Data Centre - MOHA Maseru</b>", 50, 80, 850, 390, C['orange'])

    # Firewall
    fw = d.box(
        "<b>FortiGate 100C</b><br>"
        "<span style='font-size:9px;color:#CC0000'>CRITICAL EOL - FortiOS v4.0 MR3 (2012)</span><br>"
        "<span style='font-size:9px;color:#CC0000'>No security patches since 2016</span>",
        90, 115, 250, 60, C['red'], ["shadow=1", "strokeWidth=2"])

    # Server Network
    d.group("<b>Server Network 10.151.1.0/24</b>", 90, 195, 380, 100, C['blue'])
    srv_bb = d.box("<b>BB Switches</b><br><span style='font-size:9px'>Cisco 3750X</span>",
                   110, 235, 110, 40, C['blue'], ["shadow=1"])
    srv_sw = d.box("<b>Server Switches</b><br><span style='font-size:9px'>Cisco 2960</span>",
                   235, 235, 110, 40, C['blue'], ["shadow=1"])
    srv_c = d.box("<b>18 Servers</b><br><span style='font-size:9px'>IBM/HP rack</span>",
                  360, 235, 90, 40, C['blue'], ["shadow=1"])

    # SAN
    d.group("<b>SAN Fabric</b>", 500, 195, 370, 100, C['teal'])
    san1 = d.box("<b>SAN-SW1/2</b><br><span style='font-size:9px'>Cisco MDS 9148</span>",
                 520, 235, 130, 40, C['teal'], ["shadow=1"])
    emc = d.cylinder("<b>EMC VNX</b><br><span style='font-size:9px'>Primary</span>",
                     680, 228, 75, 52, C['teal'])
    ibm = d.cylinder("<b>IBM V7000</b><br><span style='font-size:9px'>DR</span>",
                     780, 228, 75, 52, C['teal'])

    # User Network
    d.group("<b>User Network 10.50.1.0/24</b>", 90, 315, 380, 80, C['green'])
    d.box("<b>Access Switches</b><br><span style='font-size:9px'>Cisco 2960</span>",
          110, 348, 120, 35, C['green'], ["shadow=1"])
    d.box("<b>Workstations</b><br><span style='font-size:9px'>~50 PCs</span>",
          250, 348, 100, 35, C['green'], ["shadow=1"])

    # DC Routers
    rtr = d.box("<b>DC Routers</b><br><span style='font-size:9px'>HSRP Cluster VIP 10.141.1.1</span>",
                500, 350, 200, 40, C['blue'], ["shadow=1"])

    # WAN
    wan = d.cloud("<b>Government WAN</b><br>MICSTI Fiber Network",
                  300, 500, 350, 100, C['gray'])

    # Remote Sites
    pp = d.box("<b>Passport Offices (10)</b><br>"
               "<span style='font-size:9px'>50-100 Mbps fiber</span><br>"
               "<span style='font-size:9px'>SDIS + eBCS workstations</span>",
               30, 640, 190, 65, C['green'], ["shadow=1"])
    abp = d.box("<b>Automated Border Posts (8)</b><br>"
                "<span style='font-size:9px'>20 Mbps links</span><br>"
                "<span style='font-size:9px'>eBCS + biometric readers</span>",
                240, 640, 190, 65, C['blue'], ["shadow=1"])
    dist = d.box("<b>District Offices (10)</b><br>"
                 "<span style='font-size:9px'>CR + NICR services</span><br>"
                 "<span style='font-size:9px'>VPN over fiber</span>",
                 450, 640, 190, 65, C['green'], ["shadow=1"])
    mbp = d.box("<b>Manual Border Posts (5)</b><br>"
                "<span style='font-size:9px;color:#CC0000'>NO electronic systems</span><br>"
                "<span style='font-size:9px;color:#CC0000'>Paper-based only</span>",
                660, 640, 170, 65, C['red'], ["shadow=1"])
    lrmis = d.box("<b>LRMIS Centres (60+)</b><br>"
                  "<span style='font-size:9px;color:#F57F17'>Limited/no connectivity</span>",
                  850, 640, 160, 65, C['yellow'], ["shadow=1"])

    d.connect(rtr, wan, "", "#666666")
    d.connect(wan, pp, "", C['green']['stroke'])
    d.connect(wan, abp, "", C['blue']['stroke'])
    d.connect(wan, dist, "", C['green']['stroke'])
    d.connect(wan, mbp, "", C['red']['stroke'], dashed=True)
    d.connect(wan, lrmis, "", C['yellow']['stroke'], dashed=True)

    fname = "02_network_architecture.drawio"
    d.save(os.path.join(OUT_DIR, fname))
    return fname


# ============================================================
# Diagram 03: Server Infrastructure
# ============================================================
def diagram_03():
    d = DrawioBuilder("Server Infrastructure", 1100, 620)

    d.title("<b>Server Infrastructure Overview</b>", 200, 10, 700, 35)
    d.subtitle("DHA Lesotho - 18 Servers in Central Data Centre", 200, 45, 700, 25)

    y0 = 80
    c1, c2, c3 = 30, 380, 730

    # Oracle RAC - Passport
    d.group("<b>Oracle RAC - Passport</b>", c1, y0, 320, 130, C['blue'])
    d.box("<b>LESORA01</b><br><span style='font-size:9px'>IBM X3850 x5 | RHEL 6.3</span><br><span style='font-size:9px'>64GB RAM | Oracle 11G</span>",
          c1+15, y0+35, 135, 55, C['blue'], ["shadow=1"])
    d.box("<b>LESORA02</b><br><span style='font-size:9px'>IBM X3850 x5 | RHEL 6.3</span><br><span style='font-size:9px'>64GB RAM | Oracle 11G</span>",
          c1+165, y0+35, 135, 55, C['blue'], ["shadow=1"])
    d.box("<span style='font-size:9px;color:#2E7D32'>Active-Active Cluster</span>",
          c1+80, y0+97, 140, 20, C['green'], ["fontSize=9"])

    # Oracle RAC - Civil Reg
    d.group("<b>Oracle RAC - Civil Registration</b>", c2, y0, 320, 130, C['green'])
    d.box("<b>DBCR-LES01</b><br><span style='font-size:9px'>IBM X3850 x5 | RHEL 6.0</span><br><span style='font-size:9px'>64GB RAM | Oracle 11G</span>",
          c2+15, y0+35, 135, 55, C['green'], ["shadow=1"])
    d.box("<b>DBCR-LES02</b><br><span style='font-size:9px'>IBM X3850 x5 | RHEL 6.0</span><br><span style='font-size:9px'>64GB RAM | Oracle 11G</span>",
          c2+165, y0+35, 135, 55, C['green'], ["shadow=1"])
    d.box("<span style='font-size:9px;color:#2E7D32'>Active-Active Cluster</span>",
          c2+80, y0+97, 140, 20, C['green'], ["fontSize=9"])

    # AFIS
    d.group("<b>AFIS - NOT Clustered</b>", c3, y0, 280, 130, C['red'])
    d.box("<b>AFIS01</b><br><span style='font-size:9px'>HP DL 360 | Debian 8.1</span><br><span style='font-size:9px'>64GB RAM</span>",
          c3+15, y0+35, 115, 50, C['red'], ["shadow=1"])
    d.box("<b>AFIS02</b><br><span style='font-size:9px'>HP DL 360 | Debian 8.1</span><br><span style='font-size:9px'>64GB RAM</span>",
          c3+145, y0+35, 115, 50, C['red'], ["shadow=1"])
    d.box("<span style='font-size:9px;color:#CC0000'>SPOF - No failover</span>",
          c3+60, y0+97, 150, 20, C['red'], ["fontSize=9"])

    # Row 2
    y2 = y0 + 155
    d.group("<b>KMS - ePassport PKI</b>", c1, y2, 320, 115, C['blue'])
    for i, nm in enumerate(["KMS-LES01", "KMS-LES02", "KMS-LES03"]):
        d.box(f"<b>{nm}</b><br><span style='font-size:8px'>Win 2008 R2</span>",
              c1+15+i*100, y2+35, 90, 38, C['blue'], ["shadow=1"])
    d.box("<span style='font-size:9px'>+ KMS-LES04/05 Standalone</span>",
          c1+70, y2+80, 170, 20, C['blue'], ["fontSize=9"])

    d.group("<b>Document Archiving</b>", c2, y2, 320, 115, C['blue'])
    d.box("<b>DAS-LES01</b><br><span style='font-size:9px'>Win 2008 R2 | SQL 2008</span>",
          c2+15, y2+35, 130, 45, C['blue'], ["shadow=1"])
    d.box("<b>DAS-LES02</b><br><span style='font-size:9px'>Win 2008 R2 | WebLogic</span>",
          c2+165, y2+35, 130, 45, C['blue'], ["shadow=1"])

    d.group("<b>Infrastructure Services</b>", c3, y2, 280, 115, C['gray'])
    d.box("<b>DC01 / DC02</b><br><span style='font-size:9px'>Active Directory</span><br><span style='font-size:9px'>Win 2008 R2</span>",
          c3+15, y2+35, 115, 50, C['gray'], ["shadow=1"])
    d.box("<b>MANAG</b><br><span style='font-size:9px'>Monitoring</span><br><span style='font-size:9px'>RHEL 6.3</span>",
          c3+145, y2+35, 115, 50, C['gray'], ["shadow=1"])

    # Row 3
    y3 = y2 + 140
    d.group("<b>Backup Infrastructure</b>", c1, y3, 320, 95, C['yellow'])
    d.box("<b>BACKUP-LES</b><br><span style='font-size:9px'>HP Data Protector 7.0</span>",
          c1+15, y3+35, 130, 40, C['yellow'], ["shadow=1"])
    d.box("<b>CRBACKUP</b><br><span style='font-size:8px'>CR DB</span>",
          c1+160, y3+32, 70, 30, C['yellow'], ["shadow=1", "fontSize=9"])
    d.box("<b>EMCSNAP</b><br><span style='font-size:8px'>Storage</span>",
          c1+240, y3+32, 70, 30, C['yellow'], ["shadow=1", "fontSize=9"])

    # OS / DB Risk boxes
    d.box("<b>Operating Systems - ALL EOL</b><br>"
          "<span style='font-size:9px;color:#CC0000'>Windows Server 2008 R2 (11 srv) - EOL Jan 2020</span><br>"
          "<span style='font-size:9px;color:#CC0000'>RHEL 6.x (5 srv) - EOL Nov 2020</span><br>"
          "<span style='font-size:9px;color:#CC0000'>Debian 8.1 (2 srv) - EOL Jun 2020</span>",
          c2, y3, 320, 95, C['red'], ["shadow=1", "strokeWidth=2"])

    d.box("<b>Database Platforms - ALL EOL</b><br>"
          "<span style='font-size:9px;color:#CC0000'>Oracle 11G RAC (4 srv) - EOL Dec 2020</span><br>"
          "<span style='font-size:9px;color:#CC0000'>SQL Server 2008 (2 srv) - EOL Jul 2019</span>",
          c3, y3, 280, 95, C['red'], ["shadow=1", "strokeWidth=2"])

    fname = "03_server_infrastructure.drawio"
    d.save(os.path.join(OUT_DIR, fname))
    return fname


# ============================================================
# Diagram 04: Business Process Overview
# LAYOUT: Aligned rows - each process area on same row as its system
# This avoids all crossing lines
# ============================================================
def diagram_04():
    d = DrawioBuilder("Business Process Overview", 850, 680)

    d.title("<b>Business Process Overview</b>", 100, 10, 650, 35)
    d.subtitle("DHA Lesotho - Service Areas &amp; Supporting IT Systems", 100, 45, 650, 25)

    px = 30   # process x
    sx = 530  # system x
    aw = 60   # arrow gap

    # Each row: process area (left) -> IT system (right), vertically aligned
    rows = [
        ("Life Event Registration", C['green'],
         ["Birth, Marriage, Divorce, Death", "Adoption, Naturalisation <span style='color:#CC0000'>(manual)</span>"],
         "CR System", "Civil Registration", "Impala"),
        ("Identity Documents", C['blue'],
         ["National ID Card (8-step)", "Mobile ID Kit (offline)", "ePassport (11-stage)"],
         "NICR + SDIS", "ID &amp; Passport Issuance", "Impala + GET"),
        ("Border Management", C['teal'],
         ["Automated Control (8 posts + airport)", "Manual Crossing <span style='color:#CC0000'>(5 posts, paper)</span>"],
         "eBCS", "Border Control", "GET Group"),
        ("Immigration Services", C['purple'],
         ["eResidence Permits", "Visa <span style='color:#CC0000'>(INACTIVE)</span>, Deportation <span style='color:#CC0000'>(manual)</span>"],
         "ResPerm", "eResidence Permits", "Atlantic Hi Tech"),
        ("Identity Verification", C['orange'],
         ["KYC / Bank Verification", "SIM Registration, Gov services"],
         "GI System", "Generic Interface", "Impala"),
        ("Livestock Registration", C['yellow'],
         ["Cattle Registration, Brand Mgmt", "60+ Resource Centres"],
         "LRMIS", "Livestock System", "CBS"),
    ]

    y = 82
    proc_ids = []
    sys_ids = []
    for proc_name, color, items, sys_name, sys_desc, vendor in rows:
        item_html = "<br>".join([f"<span style='font-size:9px'>&#8226; {it}</span>" for it in items])
        bh = max(len(items) * 17 + 8, 40)

        # Process header + items
        d.header(f"<b>{proc_name}</b>", px, y, 240, 26, color)
        pid = d.box(item_html, px, y + 26, 240, bh, C['white'],
                    [f"strokeColor={color['stroke']}", "align=left", "spacingLeft=8", "verticalAlign=top"])
        proc_ids.append(pid)

        # IT System box - aligned on same row
        sys_h = bh + 26
        sid = d.box(
            f"<b>{sys_name}</b><br><span style='font-size:9px'>{sys_desc}</span><br>"
            f"<span style='font-size:8px;color:#888'>{vendor}</span>",
            sx, y, 180, sys_h, color, ["shadow=1"])
        sys_ids.append(sid)

        # Arrow: process -> system (horizontal, no crossing possible)
        d.connect_lr(pid, sid, "", color['stroke'])

        y += sys_h + 14

    # AFIS - below, connected to row 1 (NICR+SDIS) only
    afis = d.hexagon("<b>AFIS</b><br><span style='font-size:9px'>Biometric deduplication</span>",
                     sx + 200, 160, 120, 55, C['red'])
    d.connect_lr(afis, sys_ids[1], "dedup", C['red']['stroke'], dashed=True)

    fname = "04_business_process_overview.drawio"
    d.save(os.path.join(OUT_DIR, fname))
    return fname


# ============================================================
# Diagram 05: Storage Architecture
# ============================================================
def diagram_05():
    d = DrawioBuilder("Storage Architecture", 1000, 600)

    d.title("<b>Storage Architecture</b>", 150, 10, 700, 35)
    d.subtitle("DHA Lesotho - SAN Fabric &amp; Storage Systems", 150, 45, 700, 25)

    # Server Farm
    d.group("<b>Server Farm</b>", 30, 80, 900, 100, C['blue'])
    srvs = [
        ("Oracle RAC<br>Passport", 50, C['blue']),
        ("Oracle RAC<br>Civil Reg", 200, C['green']),
        ("AFIS<br>Servers", 350, C['red']),
        ("KMS<br>PKI", 480, C['blue']),
        ("DAS<br>Archiving", 610, C['blue']),
        ("Backup<br>Server", 740, C['yellow']),
    ]
    srv_ids = []
    for name, x, color in srvs:
        sid = d.box(f"<b>{name}</b>", x, 115, 120, 42, color, ["shadow=1"])
        srv_ids.append(sid)

    # SAN Fabric - two switches side by side with clear dual-path
    d.group("<b>Dual-Fabric SAN</b>", 100, 220, 750, 100, C['teal'])
    sw1 = d.box("<b>SAN-SW1 (Fabric A)</b><br><span style='font-size:9px'>Cisco MDS 9148 | 32 FC ports</span>",
                140, 255, 200, 45, C['teal'], ["shadow=1"])
    sw2 = d.box("<b>SAN-SW2 (Fabric B)</b><br><span style='font-size:9px'>Cisco MDS 9148 | 32 FC ports</span>",
                600, 255, 200, 45, C['teal'], ["shadow=1"])

    # Storage
    d.group("<b>Storage Systems</b>", 30, 360, 900, 160, C['orange'])
    emc = d.cylinder("<b>EMC VNX</b><br><span style='font-size:9px'>Primary Storage</span>",
                     100, 395, 120, 75, C['orange'])
    p0 = d.box("<b>Pool 0</b><br><span style='font-size:10px'>4.28 TB</span><br><span style='font-size:9px'>Production</span>",
               250, 398, 110, 50, C['orange'], ["shadow=1"])
    p1 = d.box("<b>Pool 1</b><br><span style='font-size:10px'>4.30 TB</span><br><span style='font-size:9px'>Secondary</span>",
               380, 398, 110, 50, C['orange'], ["shadow=1"])
    d.box("<b>Total: 8.58 TB</b>", 295, 458, 130, 26, C['orange'], ["fontStyle=1", "shadow=1"])

    ibm = d.cylinder("<b>IBM V7000</b><br><span style='font-size:9px'>DR / Replication</span>",
                     570, 395, 120, 75, C['blue'])
    d.box("<b>HP Data Protector 7.0</b><br><span style='font-size:9px'>Tape Libraries</span><br><span style='font-size:9px'>Weekly full backup</span>",
          740, 398, 150, 60, C['yellow'], ["shadow=1"])

    # Connectors - left 3 servers to SW1, right 3 servers to SW2 (no crossing)
    for sid in srv_ids[:3]:
        d.connect(sid, sw1, "", C['teal']['stroke'])
    for sid in srv_ids[3:]:
        d.connect(sid, sw2, "", C['teal']['stroke'])
    # Both switches to EMC
    d.connect(sw1, emc, "FC", C['teal']['stroke'])
    d.connect(sw2, ibm, "FC", C['teal']['stroke'])
    # Cross-connections shown as labels, not extra lines
    d.connect_lr(emc, p0, "", C['orange']['stroke'])
    d.connect_lr(emc, p1, "", C['orange']['stroke'])

    fname = "05_storage_architecture.drawio"
    d.save(os.path.join(OUT_DIR, fname))
    return fname


# ============================================================
# Diagram 06: EOL Risk Overview
# ============================================================
def diagram_06():
    d = DrawioBuilder("EOL Risk Overview", 1100, 650)

    d.title("<b>End-of-Life Risk Overview</b>", 200, 10, 700, 35)
    d.subtitle("DHA Lesotho - All Infrastructure Components Past End-of-Life", 200, 45, 700, 25)

    # Timeline header
    bx = 250
    yw = 80
    years = list(range(2016, 2027))
    for i, yr in enumerate(years):
        x = bx + i * yw
        c = C['blue'] if yr == 2026 else C['light_gray']
        d.box(f"<b>{yr}</b>", x, 78, yw, 22, c, ["fontSize=9"])

    # Assessment marker
    ax = bx + 10 * yw
    d.box("<b>Assessment<br>March 2026</b>", ax + 5, 102, 70, 32, C['dark_blue'], ["fontSize=8", "shadow=1"])

    cats = [
        ("Server Operating Systems", [
            ("Windows Server 2008 R2", "11 servers", 2020, 1),
            ("RHEL 6.x", "5 servers", 2020, 11),
            ("Debian 8.1", "2 servers (AFIS)", 2020, 6),
        ]),
        ("Database Platforms", [
            ("Oracle 11G RAC", "4 servers", 2020, 12),
            ("SQL Server 2008", "2 servers", 2019, 7),
        ]),
        ("Network &amp; Security", [
            ("Cisco IOS 12.2", "DC switches", 2018, 1),
            ("FortiGate v4.0 MR3", "Firewall", 2016, 1),
            ("Cisco MDS NX-OS 5.0", "SAN switches", 2018, 6),
        ]),
    ]

    y = 145
    for cat_name, items in cats:
        d.header(f"<b>{cat_name}</b>", 30, y, 200, 25, C['gray'])
        y += 32

        for name, detail, eol_yr, eol_mo in items:
            d.box(f"<b>{name}</b><br><span style='font-size:8px;color:#666'>{detail}</span>",
                  30, y, 200, 32, C['white'], [f"strokeColor={C['red']['stroke']}", "align=left", "spacingLeft=8"])

            eol_x = bx + (eol_yr - 2016) * yw + int((eol_mo / 12) * yw)
            bar_w = bx + 11 * yw - eol_x
            d.box(f"<span style='font-size:8px'>EOL {eol_mo}/{eol_yr}</span>",
                  eol_x, y + 4, max(bar_w, 50), 22, C['red'], ["fontSize=8"])

            yrs_past = 2026 - eol_yr
            d.box(f"<b>{yrs_past}+ years</b>",
                  bx + 11 * yw + 10, y + 4, 70, 22,
                  {'fill': '#FFCCCC', 'stroke': '#CC0000', 'font': '#CC0000'}, ["fontSize=9"])

            y += 40
        y += 12

    # Summary
    d.box("<b>CRITICAL RISK SUMMARY</b><br>"
          "<span style='font-size:10px;color:#CC0000'>&#8226; 100% of server OS, databases, and network firmware are past EOL</span><br>"
          "<span style='font-size:10px;color:#CC0000'>&#8226; No security patches available for any infrastructure component</span><br>"
          "<span style='font-size:10px;color:#CC0000'>&#8226; Average time past EOL: 5-10 years</span>",
          30, y + 5, 650, 75, C['red'], ["shadow=1", "strokeWidth=2"])

    fname = "06_eol_risk_overview.drawio"
    d.save(os.path.join(OUT_DIR, fname))
    return fname


# ============================================================
# Diagram 07: Vendor Dependency
# ============================================================
def diagram_07():
    d = DrawioBuilder("Vendor Dependency", 1050, 650)

    d.title("<b>Vendor Dependency Analysis</b>", 200, 10, 600, 35)
    d.subtitle("DHA Lesotho - System Distribution by Vendor", 200, 45, 600, 25)

    vendors = [
        ("Impala Technologies / NIP Global", "44%", "4 Systems", C['green'],
         ["CR - Civil Registration", "NICR - National Identity", "GI - Generic Interface", "Mobile Registration"]),
        ("GET Group", "33%", "3 Systems", C['blue'],
         ["SDIS - ePassport Issuance", "eBCS - Border Control", "SDMS - Document Management"]),
        ("Computer Business Solutions", "11%", "1 System", C['yellow'],
         ["LRMIS - Livestock Registration"]),
        ("Atlantic Hi Tech", "11%", "1 System", C['purple'],
         ["ResPerm - eResidence Permits"]),
    ]

    y = 80
    for name, pct, count, color, systems in vendors:
        d.header(f"<b>{name}</b>", 30, y, 400, 32, color)
        d.box(f"<b style='font-size:18px'>{pct}</b><br><span style='font-size:9px'>{count}</span>",
              440, y, 80, 32, color, ["shadow=1"])

        # Bar
        bar_w = int(float(pct.replace('%', '')) / 100 * 450)
        d.box("", 530, y + 3, bar_w, 26, color, ["opacity=70"])

        for i, sn in enumerate(systems):
            d.box(f"<span style='font-size:10px'>&#8226; {sn}</span>",
                  50, y + 37 + i * 26, 380, 22, C['white'],
                  [f"strokeColor={color['stroke']}", "align=left", "spacingLeft=8"])

        y += 42 + len(systems) * 26 + 18

    # Risk box
    d.box("<b>KEY RISKS</b><br>"
          "<span style='font-size:9px;color:#CC0000'>&#8226; 77% of systems depend on just 2 vendors (Impala + GET)</span><br>"
          "<span style='font-size:9px;color:#CC0000'>&#8226; No formal SLAs or maintenance agreements documented</span><br>"
          "<span style='font-size:9px;color:#CC0000'>&#8226; AFIS vendor (not listed) - critical biometric service with SPOF</span><br>"
          "<span style='font-size:9px;color:#F57F17'>&#8226; All vendor contracts require review and renegotiation</span>",
          30, y + 8, 500, 90, C['red'], ["shadow=1", "strokeWidth=2", "align=left", "spacingLeft=10"])

    fname = "07_vendor_dependency.drawio"
    d.save(os.path.join(OUT_DIR, fname))
    return fname


# ============================================================
# Diagram 08: Passport Issuance Flow
# ============================================================
def diagram_08():
    d = DrawioBuilder("Passport Issuance Flow", 750, 950)

    d.title("<b>ePassport Issuance Process Flow</b>", 50, 10, 650, 35)
    d.subtitle("DHA Lesotho - 11-Stage End-to-End Process (SDIS)", 50, 45, 650, 25)

    cx = 55

    # Phase 1
    d.group("<b>Phase 1: Enrollment (District Office)</b>", 30, 75, 420, 290, C['green'])
    p1_steps = [
        ("1. Application Registration", "Biographic data capture"),
        ("2. Biometric Enrollment", "Face + 10 Fingerprints + Signature"),
        ("3. Payment Processing", "Fee collection &amp; receipt"),
        ("4. Document Scanning", "Supporting docs digitized"),
        ("5. Site Audit", "Local verification &amp; approval"),
    ]
    prev = None
    for i, (name, detail) in enumerate(p1_steps):
        s = d.box(f"<b>{name}</b><br><span style='font-size:9px;color:#666'>{detail}</span>",
                  cx, 112 + i * 50, 370, 38, C['green'], ["shadow=1"])
        if prev:
            d.connect(prev, s, "", C['green']['stroke'])
        prev = s

    # Network transfer
    net = d.box("<b>6. Data Transfer to Central</b><br>"
                "<span style='font-size:9px;color:#F57F17'>VPN over Gov WAN | Offline fallback: USB courier</span>",
                cx, 380, 370, 40, C['yellow'], ["shadow=1", "strokeWidth=2"])
    d.connect(prev, net, "", C['green']['stroke'])

    # Phase 2
    d.group("<b>Phase 2: Central Processing (Maseru HQ)</b>", 30, 435, 420, 210, C['blue'])
    p2_steps = [
        ("7. Stop List Validation", "Check against stop lists"),
        ("8. Passport Printing", "E2000 printer + ECCD chip personalization"),
        ("9. Quality Assurance", "MRZ, Chip, UV/IR verification"),
    ]
    prev = net
    for i, (name, detail) in enumerate(p2_steps):
        s = d.box(f"<b>{name}</b><br><span style='font-size:9px;color:#666'>{detail}</span>",
                  cx, 475 + i * 55, 370, 38, C['blue'], ["shadow=1"])
        d.connect(prev, s, "", C['blue']['stroke'])
        prev = s

    # Phase 3
    d.group("<b>Phase 3: Delivery</b>", 30, 660, 420, 130, C['teal'])
    p3_steps = [
        ("10. Dispatch via Post Office", "Courier to collection point"),
        ("11. Delivery to Applicant", "Fingerprint verification at collection"),
    ]
    for i, (name, detail) in enumerate(p3_steps):
        s = d.box(f"<b>{name}</b><br><span style='font-size:9px;color:#666'>{detail}</span>",
                  cx, 695 + i * 45, 370, 35, C['teal'], ["shadow=1"])
        d.connect(prev, s, "", C['teal']['stroke'])
        prev = s

    # Side info
    d.box("<b>Related Systems</b><br>"
          "<span style='font-size:9px'>&#8226; SDIS - Main issuance system</span><br>"
          "<span style='font-size:9px'>&#8226; SDMS - Document management</span><br>"
          "<span style='font-size:9px'>&#8226; AFIS - Deduplication checks</span><br>"
          "<span style='font-size:9px'>&#8226; KMS - PKI certificate signing</span><br>"
          "<span style='font-size:9px'>&#8226; Stop Lists - Watchlist validation</span>",
          490, 120, 200, 115, C['gray'], ["shadow=1", "align=left", "spacingLeft=8"])

    d.box("<b>Capacity</b><br>"
          "<span style='font-size:9px'>&#8226; 300K passports/year design</span><br>"
          "<span style='font-size:9px'>&#8226; 10 enrollment offices</span><br>"
          "<span style='font-size:9px'>&#8226; 1 central production site</span>",
          490, 260, 200, 75, C['blue'], ["shadow=1", "align=left", "spacingLeft=8"])

    fname = "08_passport_issuance_flow.drawio"
    d.save(os.path.join(OUT_DIR, fname))
    return fname


# ============================================================
# Diagram 09: Border Control Flow
# ============================================================
def diagram_09():
    d = DrawioBuilder("Border Control Flow", 800, 900)

    d.title("<b>Border Control Process Flow</b>", 100, 10, 600, 35)
    d.subtitle("DHA Lesotho - eBCS Automated Verification (5 Validation Steps)", 100, 45, 600, 25)

    cx = 250

    start = d.box("<b>Traveller Arrival</b>", cx, 80, 180, 32, C['gray'], ["shadow=1"])
    gate = d.box("<b>Approach Gate</b><br><span style='font-size:9px'>Document presented</span>",
                 cx, 130, 180, 38, C['blue'], ["shadow=1"])
    d.connect(start, gate, "", "#666666")

    doc = d.box("<b>Document Reading</b><br><span style='font-size:9px'>MRZ scan + chip read</span>",
                cx, 186, 180, 38, C['blue'], ["shadow=1"])
    d.connect(gate, doc, "", C['blue']['stroke'])

    bio = d.box("<b>Biometric Capture</b><br><span style='font-size:9px'>Fingerprint scan</span>",
                cx, 242, 180, 38, C['blue'], ["shadow=1"])
    d.connect(doc, bio, "", C['blue']['stroke'])

    validations = [
        ("V1", "MRZ / Chip Data Integrity"),
        ("V2", "In/Out Status Consistency"),
        ("V3", "Validation Rules<br><span style='font-size:8px'>(forbidden, quarantine, overstay)</span>"),
        ("V4", "Stop List Check"),
        ("V5", "Fingerprint Match vs SDIS"),
    ]

    prev = bio
    vy = 305
    fail_ids = []
    for code, desc in validations:
        dm = d.diamond(f"<b>{code}</b><br><span style='font-size:8px'>{desc}</span>",
                       cx + 15, vy, 150, 80, C['yellow'])
        d.connect(prev, dm, "", C['blue']['stroke'])

        fail = d.box("<span style='font-size:8px;color:#CC0000'>FAIL</span>",
                     cx + 200, vy + 20, 45, 22,
                     {'fill': '#FFFFFF', 'stroke': '#CC0000', 'font': '#CC0000'})
        d.connect_lr(dm, fail, "", C['red']['stroke'])
        fail_ids.append(fail)

        prev = dm
        vy += 90

    # Outcomes
    approved = d.box("<b>APPROVED</b><br><span style='font-size:9px'>Entry/Exit recorded</span>",
                     cx, vy + 10, 180, 42, C['green'], ["shadow=1", "strokeWidth=2"])
    d.connect(prev, approved, "PASS", C['green']['stroke'])

    rejected = d.box("<b>REJECTED</b><br><span style='font-size:9px'>Secondary inspection / Denial</span>",
                     cx + 240, vy + 10, 180, 42, C['red'], ["shadow=1", "strokeWidth=2"])
    # Connect last fail to rejected
    d.connect_lr(fail_ids[-1], rejected, "", C['red']['stroke'])

    # Coverage box
    d.box("<b>Border Post Coverage</b><br>"
          "<span style='font-size:9px;color:#2E7D32'>&#8226; 8 Automated Land Posts (eBCS)</span><br>"
          "<span style='font-size:9px;color:#2E7D32'>&#8226; 1 Airport (Moshoeshoe I)</span><br>"
          "<span style='font-size:9px;color:#CC0000'>&#8226; 5 Manual Posts (NO eBCS)</span><br>"
          "<span style='font-size:9px;color:#CC0000'>&#8226; Manual = paper logbook only</span>",
          30, 90, 190, 95, C['gray'], ["shadow=1", "align=left", "spacingLeft=8"])

    fname = "09_border_control_flow.drawio"
    d.save(os.path.join(OUT_DIR, fname))
    return fname


# ============================================================
# Diagram 10: Site Distribution
# ============================================================
def diagram_10():
    d = DrawioBuilder("Site Distribution", 950, 700)

    d.title("<b>Site Distribution</b>", 100, 10, 700, 35)
    d.subtitle("DHA Lesotho - Geographic Distribution of IT Infrastructure", 100, 45, 700, 25)

    # HQ - top center, NO repeated server/storage details (belong in D03/D05)
    hq = d.box("<b>Maseru HQ</b><br>"
               "<span style='font-size:9px'>Data Centre + DHA Head Office</span><br>"
               "<span style='font-size:9px;color:#666'>Central production &amp; admin site</span>",
               330, 80, 250, 65, C['orange'], ["shadow=1", "strokeWidth=2"])

    # Districts - connectors from HQ go straight down
    dg = d.group("<b>10 Districts - each with District Office + Passport Office</b>",
                 30, 185, 870, 115, C['green'])
    districts = ["Maseru", "Berea", "Leribe", "Butha-Buthe", "Mokhotlong",
                 "Thaba-Tseka", "Qacha's Nek", "Quthing", "Mohale's Hoek", "Mafeteng"]
    for i, nm in enumerate(districts):
        x = 50 + (i % 5) * 170
        y = 225 + (i // 5) * 38
        d.box(f"<b>{nm}</b>",
              x, y, 150, 25, C['green'], ["shadow=1", "fontSize=10"])
    d.connect(hq, dg, "Fiber WAN (50-100 Mbps)", C['green']['stroke'])

    # Border Posts row - side by side, NOT overlapping with Districts connector
    bg = d.group("<b>Automated Border Posts (9) - eBCS</b>", 30, 340, 530, 110, C['blue'])
    auto_posts = ["Maseru Bridge", "Ficksburg Bridge", "Caledonspoort",
                  "Van Rooyens Gate", "Maputsoe Bridge", "Qacha's Nek",
                  "Tele Bridge", "Sani Pass", "Moshoeshoe I Airport"]
    for i, nm in enumerate(auto_posts):
        x = 48 + (i % 3) * 175
        y = 378 + (i // 3) * 24
        d.box(f"<span style='font-size:8px'><b>{nm}</b></span>",
              x, y, 160, 18, C['blue'], ["shadow=1", "fontSize=8"])

    mg = d.group("<b>Manual Border Posts (5)</b>", 590, 340, 300, 110, C['red'])
    manual_posts = ["Ongeluksnek", "Ramatsilitso", "Makhaleng", "Sekakes", "Moteng Pass"]
    for i, nm in enumerate(manual_posts):
        d.box(f"<span style='font-size:8px'><b>{nm}</b></span>",
              610, 378 + i * 18, 110, 15, C['red'], ["fontSize=8"])
    d.box("<span style='font-size:8px;color:#CC0000'>NO electronic<br>systems</span>",
          740, 385, 95, 35, C['red'], ["fontSize=8"])

    # Connectors from Districts group (not HQ) to avoid crossing
    d.connect(dg, bg, "VPN 20 Mbps", C['blue']['stroke'])
    d.connect(dg, mg, "", C['red']['stroke'], dashed=True)

    # LRMIS
    d.group("<b>LRMIS Resource Centres (60+)</b>", 30, 490, 380, 65, C['yellow'])
    d.box("<span style='font-size:9px'>All 10 districts | Limited/no WAN - standalone</span>",
          50, 518, 340, 25, C['yellow'])

    # Summary
    d.box("<b>Site Summary</b><br>"
          "<span style='font-size:9px;color:#2E7D32'>&#8226; 1 Data Centre (Maseru)</span><br>"
          "<span style='font-size:9px;color:#2E7D32'>&#8226; 10 District + 10 Passport Offices</span><br>"
          "<span style='font-size:9px;color:#0D47A1'>&#8226; 9 Automated Border Posts</span><br>"
          "<span style='font-size:9px;color:#CC0000'>&#8226; 5 Manual Border Posts</span><br>"
          "<span style='font-size:9px;color:#F57F17'>&#8226; 60+ LRMIS Centres</span><br>"
          "<span style='font-size:9px'><b>Total: ~95+ sites</b></span>",
          500, 490, 200, 120, C['gray'], ["shadow=1", "align=left", "spacingLeft=8"])

    fname = "10_site_distribution.drawio"
    d.save(os.path.join(OUT_DIR, fname))
    return fname


# ============================================================
# Export
# ============================================================
def export_to_png(drawio_file, scale=2):
    infile = os.path.join(OUT_DIR, drawio_file)
    outfile = os.path.join(OUT_DIR, drawio_file.replace('.drawio', '.png'))
    cmd = [DRAWIO_EXE, '--export', '--format', 'png',
           '--scale', str(scale), '--output', outfile, infile]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if os.path.exists(outfile):
            size = os.path.getsize(outfile)
            print(f"  PNG: {os.path.basename(outfile)} ({size:,} bytes)")
            return True
        else:
            print(f"  FAILED: {drawio_file}: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ERROR: {drawio_file}: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("LESICT01 Inception Report - Diagram Generation")
    print("=" * 60)

    diagram_funcs = [
        ("01", "IT Systems Integration Map", diagram_01),
        ("02", "Network Architecture", diagram_02),
        ("03", "Server Infrastructure", diagram_03),
        ("04", "Business Process Overview", diagram_04),
        ("05", "Storage Architecture", diagram_05),
        ("06", "EOL Risk Overview", diagram_06),
        ("07", "Vendor Dependency", diagram_07),
        ("08", "Passport Issuance Flow", diagram_08),
        ("09", "Border Control Flow", diagram_09),
        ("10", "Site Distribution", diagram_10),
    ]

    files = []
    for num, name, func in diagram_funcs:
        print(f"\n[{num}/10] {name}")
        fname = func()
        files.append(fname)
        print(f"  Created: {fname}")

    print("\n" + "=" * 60)
    print("Exporting to PNG...")
    print("=" * 60)

    if not os.path.exists(DRAWIO_EXE):
        print(f"\nWARNING: draw.io not found at: {DRAWIO_EXE}")
        print("Skipping PNG export.")
    else:
        ok = sum(1 for f in files if export_to_png(f))
        print(f"\n{ok}/{len(files)} diagrams exported to PNG")

    print(f"\nOutput: {OUT_DIR}")
