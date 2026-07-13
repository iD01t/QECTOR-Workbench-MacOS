import matplotlib
print("mpl", matplotlib.__version__)
import qector_decoder_v3 as qd
from qector_decoder_v3 import codes
c = codes.ring_code(6)
print("name:", repr(c.name))
print("desc:", repr(c.description)[:120])
print("distance:", c.distance, "callable:", callable(getattr(type(c), "distance", None)))
mqd = getattr(c, "max_qubit_degree", None)
print("max_qubit_degree:", mqd, "callable:", callable(mqd))
pcm = getattr(c, "parity_check_matrix", None)
print("pcm callable:", callable(pcm))
m = pcm() if callable(pcm) else pcm
print("pcm type:", type(m), getattr(m, "shape", None))
lm = c.logicals_matrix
print("logicals_matrix callable:", callable(lm))
r = codes.rotated_surface_code(5)
print("rot name:", repr(r.name), r.n_qubits, r.n_checks)
mr = r.parity_check_matrix() if callable(r.parity_check_matrix) else r.parity_check_matrix
print("rot pcm type:", type(mr), getattr(mr, "shape", None))

# matplotlib headless Figure + PdfPages + SVG check
import io, tempfile, os
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_pdf import PdfPages
fig = Figure(figsize=(4, 3))
FigureCanvasAgg(fig)
ax = fig.add_subplot(111)
ax.plot([0, 1], [0, 1])
tmp = tempfile.mkdtemp()
pdf_path = os.path.join(tmp, "t.pdf")
with PdfPages(pdf_path, metadata={"Title": "t"}) as pp:
    pp.savefig(fig)
    pp.savefig(fig)
    print("pagecount:", pp.get_pagecount())
data = open(pdf_path, "rb").read()
print("pdf head:", data[:5])
print("type page count:", data.count(b"/Type /Page") - data.count(b"/Type /Pages"))
svg_path = os.path.join(tmp, "t.svg")
fig.savefig(svg_path, format="svg", metadata={"Title": "hello title"})
import xml.etree.ElementTree as ET
root = ET.parse(svg_path).getroot()
print("svg root:", root.tag)
print("title in svg:", "hello title" in open(svg_path, encoding="utf-8").read())
