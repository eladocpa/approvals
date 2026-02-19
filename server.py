"""
מחולל אישורים פיננסיים - שרת Web מקומי
הפעל: python server.py  |  פתח: http://localhost:5000
"""
from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader, PdfWriter
from bidi.algorithm import get_display
import io, os, datetime, re, sys

# FinBot integration (optional - only if finbot.py exists)
FINBOT_AVAILABLE = False
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import finbot as _finbot
    FINBOT_AVAILABLE = True
except Exception:
    pass

app = Flask(__name__)
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
TAMAT_PDF    = os.path.join(BASE_DIR, "templates", "daycare_daycare-subsidies-2024-2025_appendix-4-support-tests.pdf")
MORTGAGE_PDF = os.path.join(BASE_DIR, "templates", "אישורי משכנתא.pdf")

SCALE  = 3
PDF_W  = 595.32
PDF_H  = 841.92
IMG_W  = int(PDF_W * SCALE)
IMG_H  = int(PDF_H * SCALE)


def find_font(size):
    for p in [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\Arial.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def prepare_text(text):
    """Convert Hebrew text to correct visual order for PIL using BiDi algorithm."""
    if not text:
        return ""
    text = str(text).strip()
    if not text:
        return ""
    return get_display(text)


def fill_pdf(template_path, fields):
    reader = PdfReader(template_path)
    writer = PdfWriter()
    by_page = {}
    for f in fields:
        by_page.setdefault(f["page"], []).append(f)

    for page_idx, page in enumerate(reader.pages, start=1):
        if page_idx in by_page:
            overlay = Image.new("RGBA", (IMG_W, IMG_H), (0, 0, 0, 0))
            draw    = ImageDraw.Draw(overlay)
            for f in by_page[page_idx]:
                txt = prepare_text(f.get("text", ""))
                if not txt:
                    continue
                font = find_font(int(f.get("fs", 9) * SCALE))
                draw.text(
                    (int(f["x_right"] * SCALE), int(f["y_top"] * SCALE)),
                    txt, font=font, fill=(0, 0, 0, 255), anchor="rt"
                )

            png_buf = io.BytesIO()
            overlay.save(png_buf, format="PNG")
            png_buf.seek(0)

            packet = io.BytesIO()
            c = rl_canvas.Canvas(packet, pagesize=(PDF_W, PDF_H))
            c.drawImage(ImageReader(png_buf), 0, 0,
                        width=PDF_W, height=PDF_H, mask="auto")
            c.save()
            packet.seek(0)
            page.merge_page(PdfReader(packet).pages[0])

        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()


def today():
    return datetime.date.today().strftime("%d/%m/%Y")


def tamat_fields(d):
    t = today()
    return [
        {"page":1,"x_right":526,"y_top":158,"text":d.get("accountant_name","")},
        {"page":1,"x_right":334,"y_top":158,"text":d.get("license_number","")},
        {"page":1,"x_right":520,"y_top":193,"text":d.get("phone","")},
        {"page":1,"x_right":340,"y_top":193,"text":d.get("address","")},
        {"page":1,"x_right":535,"y_top":288,"text":d.get("client_name","")},
        {"page":1,"x_right":450,"y_top":288,"text":d.get("client_id","")},
        {"page":1,"x_right":235,"y_top":288,"text":d.get("business_role","בעל עסק")},
        {"page":1,"x_right":534,"y_top":330,"text":d.get("role_start_date","")},
        {"page":1,"x_right":420,"y_top":330,"text":d.get("business_name","")},
        {"page":1,"x_right":200,"y_top":330,"text":d.get("business_address","")},
        {"page":1,"x_right":525,"y_top":373,"text":d.get("income_tax_open_date","")},
        {"page":1,"x_right":285,"y_top":403,"text":d.get("vat_open_date","")},
        {"page":1,"x_right":464,"y_top":473,"text":d.get("from_month","")},
        {"page":1,"x_right":354,"y_top":473,"text":d.get("from_year","")},
        {"page":1,"x_right":464,"y_top":500,"text":d.get("to_month","")},
        {"page":1,"x_right":354,"y_top":500,"text":d.get("to_year","")},
        {"page":1,"x_right":467,"y_top":535,"text":d.get("total_income",""),"fs":10},
        {"page":1,"x_right":498,"y_top":567,"text":d.get("accountant_name","")},
        {"page":1,"x_right":242,"y_top":567,"text":t},
        {"page":1,"x_right":454,"y_top":663,"text":d.get("client_name","")},
        {"page":1,"x_right":267,"y_top":663,"text":t},
    ]


def mortgage_v1_fields(d):
    t, yr = today(), d.get("report_year","")
    return [
        {"page":1,"x_right":513,"y_top":120,"text":d.get("bank_name","")},
        {"page":1,"x_right":467,"y_top":188,"text":d.get("business_name","")},
        {"page":1,"x_right":358,"y_top":188,"text":d.get("vat_number","")},
        {"page":1,"x_right":282,"y_top":207,"text":d.get("client_name","")},
        {"page":1,"x_right":196,"y_top":207,"text":d.get("bank_name","")},
        {"page":1,"x_right":222,"y_top":222,"text":d.get("client_name","")},
        {"page":1,"x_right":152,"y_top":263,"text":yr,"fs":9},
        {"page":1,"x_right":145,"y_top":277,"text":d.get("report_submit_date",""),"fs":9},
        {"page":1,"x_right":186,"y_top":294,"text":d.get("tax_office",""),"fs":9},
        {"page":1,"x_right":131,"y_top":340,"text":yr,"fs":8},
        {"page":1,"x_right":442,"y_top":353,"text":d.get("turnover",""),"fs":10},
        {"page":1,"x_right":131,"y_top":375,"text":yr,"fs":8},
        {"page":1,"x_right":499,"y_top":389,"text":d.get("net_income",""),"fs":10},
        {"page":1,"x_right":386,"y_top":389,"text":yr,"fs":8},
        {"page":1,"x_right":131,"y_top":411,"text":yr,"fs":8},
        {"page":1,"x_right":353,"y_top":424,"text":d.get("income_tax",""),"fs":10},
        {"page":1,"x_right":461,"y_top":424,"text":yr,"fs":8},
        {"page":1,"x_right":508,"y_top":469,"text":t},
    ]


def mortgage_v2_fields(d):
    t = today()
    return [
        {"page":2,"x_right":513,"y_top":120,"text":d.get("bank_name","")},
        {"page":2,"x_right":467,"y_top":188,"text":d.get("business_name","")},
        {"page":2,"x_right":358,"y_top":188,"text":d.get("vat_number","")},
        {"page":2,"x_right":200,"y_top":188,"text":d.get("period_months",""),"fs":9},
        {"page":2,"x_right":282,"y_top":188,"text":d.get("period_end_date",""),"fs":9},
        {"page":2,"x_right":282,"y_top":207,"text":d.get("client_name","")},
        {"page":2,"x_right":196,"y_top":207,"text":d.get("bank_name","")},
        {"page":2,"x_right":222,"y_top":222,"text":d.get("client_name","")},
        {"page":2,"x_right":131,"y_top":340,"text":d.get("turnover",""),"fs":10},
        {"page":2,"x_right":131,"y_top":376,"text":d.get("net_income",""),"fs":10},
        {"page":2,"x_right":150,"y_top":419,"text":d.get("prev_report_year",""),"fs":9},
        {"page":2,"x_right":352,"y_top":433,"text":d.get("prev_submit_date",""),"fs":9},
        {"page":2,"x_right":186,"y_top":446,"text":d.get("tax_office",""),"fs":9},
        {"page":2,"x_right":144,"y_top":460,"text":d.get("credit_points",""),"fs":9},
        {"page":2,"x_right":508,"y_top":484,"text":t},
    ]


@app.route("/clients")
def get_clients():
    try:
        clients = _finbot.get_clients()
        return jsonify({"clients": clients})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/fetch_client", methods=["POST"])
def fetch_client():
    data = request.json
    data_id = data.get("data_id", "1")
    year    = data.get("year", "2025")
    try:
        result = _finbot.fetch_client_data(data_id, year)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    with open(os.path.join(BASE_DIR, "index.html"), encoding="utf-8") as f:
        return f.read()


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    ct   = data.get("cert_type", "tamat")
    print("DEBUG data:", {k:v for k,v in data.items() if v})
    try:
        if ct == "tamat":
            pdf = fill_pdf(TAMAT_PDF, tamat_fields(data))
        elif ct == "mortgage_v1":
            pdf = fill_pdf(MORTGAGE_PDF, mortgage_v1_fields(data))
        elif ct == "mortgage_v2":
            pdf = fill_pdf(MORTGAGE_PDF, mortgage_v2_fields(data))
        else:
            return jsonify({"error": "סוג לא מוכר"}), 400
        name = f"אישור_{data.get('client_name','לקוח').replace(' ','_')}.pdf"
        return send_file(io.BytesIO(pdf), mimetype="application/pdf",
                         as_attachment=True, download_name=name)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n✅ שרת פעיל! פתח: http://localhost:5000\n")
    app.run(debug=False, port=5000)
