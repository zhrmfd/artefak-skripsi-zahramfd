import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import base64
import geopandas as gpd
import os
import glob


# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="PMT & Spatial Big Data Explorer",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Function Load CSS External
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    load_css('assets/style.css')
except FileNotFoundError:
    pass

# 3. Dummy Data Amenity & Spasial
@st.cache_data
def load_amenity_data():
    data = [
        {"name": "Puskesmas Kecamatan", "category": "Kesehatan", "lat": -6.2088, "lon": 106.8456, "address": "Jl. Utama No. 12", "isochrone_min": 5},
        {"name": "RSUD Daerah", "category": "Kesehatan", "lat": -6.2150, "lon": 106.8300, "address": "Jl. Kesehatan No. 4", "isochrone_min": 12},
        {"name": "SD Negeri 01", "category": "Pendidikan", "lat": -6.1950, "lon": 106.8200, "address": "Jl. Pendidikan No. 8", "isochrone_min": 8},
        {"name": "SMA Negeri 3", "category": "Pendidikan", "lat": -6.2200, "lon": 106.8100, "address": "Jl. Kampus No. 1", "isochrone_min": 15},
        {"name": "Taman Publik Terbuka", "category": "Ruang Terbuka", "lat": -6.2000, "lon": 106.8400, "address": "Jl. Hijau No. 5", "isochrone_min": 3},
        {"name": "Pasar Tradisional", "category": "Komersial", "lat": -6.2100, "lon": 106.8500, "address": "Jl. Pasar No. 20", "isochrone_min": 10},
        {"name": "Supermarket Utama", "category": "Komersial", "lat": -6.1980, "lon": 106.8280, "address": "Jl. Niaga No. 90", "isochrone_min": 7},
    ]
    return pd.DataFrame(data)

df_amenities = load_amenity_data()

# Managing Navigation State
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Home"

# 1. Baca Query Params dari URL
query_params = st.query_params

# Set default page atau ambil dari URL parameter
if "page" in query_params:
    st.session_state['current_page'] = query_params["page"]
elif 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Home"

# 1. Fungsi untuk membaca gambar lokal dan diubah jadi string Base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Convert gambar local dari folder assets
try:
    bg_base64 = get_base64_image("assets/bg.jpg")
    bg_style = f"data:image/jpeg;base64,{bg_base64}"
except Exception:
    bg_style = "bg.jpg" # fallback

# Header Custom Component Floating & Fixed dengan Bootstrap Icons
st.markdown(f"""
    <div class="custom-header-wrapper">
        <div class="custom-header">
            <div class="header-logo">
                <i class="bi bi-globe-americas"></i> GeoInsight
            </div>
            <div class="header-menu">
                <a href="?page=Home" target="_self" class="nav-link {'active' if st.session_state['current_page'] == 'Home' else ''}">
                    <i class="bi bi-house-door"></i> Home
                </a>
                <a href="?page=Peta+Interaktif" target="_self" class="nav-link {'active' if st.session_state['current_page'] == 'Peta Interaktif' else ''}">
                    <i class="bi bi-pin-map"></i> Peta Interaktif
                </a>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# =============================================================================
# HALAMAN 1: HOME (Sesuai Pedoman Body 1 & Body 2)
# =============================================================================
if st.session_state['current_page'] == "Home":
    
    # ------------------ BODY 1: SLIDESHOW HERO ------------------
    slideshow_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
        <style>
            * {{ font-family: 'Plus Jakarta Sans', sans-serif; box-sizing: border-box; margin: 0; padding: 0; }}
            
            .hero-wrapper {{
                position: relative;
                width: 100%;
                height: 340px;
                border-radius: 16px;
                background: linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)), url('{bg_style}');
                background-size: cover;
                background-position: center;
                display: flex;
                align-items: center;
                padding: 35px;
                box-shadow: 0 8px 24px rgba(19, 42, 19, 0.25);
            }}

            .hero-card-box {{
                position: relative;
                background: rgba(19, 42, 19, 0.85);
                backdrop-filter: blur(8px);
                border: 1px solid rgba(236, 243, 158, 0.3);
                border-left: 6px solid #F6AA1C;
                border-radius: 12px;
                padding: 25px 30px;
                max-width: 600px;
                width: 100%;
                color: #FFFCF2;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            }}

            .slide-item {{ display: none; }}
            .slide-item.active {{ display: block; animation: fadeIn 0.6s ease-in-out forwards; }}
            .slide-badge {{ background-color: #941B0C; color: #FFFCF2; font-size: 0.75rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; display: inline-block; margin-bottom: 10px; text-transform: uppercase; }}
            .slide-heading {{ font-size: 1.05rem; font-weight: 400; line-height: 1.5; color: #FFFCF2; }}
            .slide-number {{ font-size: 2rem; font-weight: 800; color: #ECF39E; margin-top: 6px; }}
            
            /* Container Bawah: Dots + Next Button */
            .slide-footer {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 18px;
            }}

            .slide-dots {{ display: flex; gap: 8px; align-items: center; }}
            .dot {{ width: 8px; height: 8px; border-radius: 50%; background-color: rgba(255, 252, 242, 0.3); transition: all 0.3s ease; }}
            .dot.active {{ background-color: #F6AA1C; width: 22px; border-radius: 10px; }}

            /* Styling Tombol Next Chevron */
            .next-btn {{
                background: rgba(255, 252, 242, 0.15);
                border: 1px solid rgba(236, 243, 158, 0.4);
                color: #ECF39E;
                width: 34px;
                height: 34px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
                font-size: 1.1rem;
            }}

            .next-btn:hover {{
                background: #F6AA1C;
                color: #132A13;
                border-color: #F6AA1C;
                transform: scale(1.08);
            }}

            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(6px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
        </style>
    </head>
    <body style="background: transparent;">
        <div class="hero-wrapper">
            <div class="hero-card-box">
                <!-- SLIDE 1 -->
                <div class="slide-item active" id="slide1">
                    <span class="slide-badge">RPJMN 2025-2029</span>
                    <div class="slide-heading">
                        Rencana Pembangunan Jangka Menengah Nasional (RPJMN) tahun 2025-2029 menargetkan tingkat kemiskinan pada tahun 2025 berkisar pada angka:
                    </div>
                    <div class="slide-number">7 - 8%</div>
                </div>

                <!-- SLIDE 2 -->
                <div class="slide-item" id="slide2">
                    <span class="slide-badge">DATA BPS 2025</span>
                    <div class="slide-heading">
                        Badan Pusat Statistik (BPS) merilis data persentase penduduk miskin pada tahun 2025 semester II mencapai:
                    </div>
                    <div class="slide-number">8,25%</div>
                </div>

                <!-- FOOTER: DOTS & NEXT BUTTON -->
                <div class="slide-footer">
                    <div class="slide-dots">
                        <div class="dot active" id="dot1"></div>
                        <div class="dot" id="dot2"></div>
                    </div>
                    <button class="next-btn" onclick="manualNextSlide()" title="Slide Selanjutnya">
                        <i class="bi bi-chevron-right"></i>
                    </button>
                </div>
            </div>
        </div>

        <script>
            let current = 1;
            let slideTimer;

            function runSlideshow() {{
                const s1 = document.getElementById('slide1');
                const s2 = document.getElementById('slide2');
                const d1 = document.getElementById('dot1');
                const d2 = document.getElementById('dot2');

                if (current === 1) {{
                    s1.classList.remove('active');
                    s2.classList.add('active');
                    d1.classList.remove('active');
                    d2.classList.add('active');
                    current = 2;
                }} else {{
                    s2.classList.remove('active');
                    s1.classList.add('active');
                    d2.classList.remove('active');
                    d1.classList.add('active');
                    current = 1;
                }}
            }}

            // Fungsi Timer Otomatis
            function startTimer() {{
                slideTimer = setInterval(runSlideshow, 15000);
            }}

            // Fungsi jika user klik tombol Next secara manual
            function manualNextSlide() {{
                clearInterval(slideTimer); // Hentikan timer lama
                runSlideshow();             
                startTimer();              
            }}

            // Jalankan timer pertama kali
            startTimer();
        </script>
    </body>
    </html>
    """

    st.components.v1.html(slideshow_html, height=360)

    # ------------------ BODY 2: PROXY MEANS TEST (PMT) ------------------
    st.markdown("""
        <div class="pmt-container">
            <div class="pmt-title">Proxy Means Test (PMT)</div>
            <div class="pmt-desc">
                Adalah metode yang memanfaatkan informasi mengenai karakteristik rumah tangga untuk mendapatkan hasil prediksi pengeluaran rumah tangga.
            </div>
            <div class="pmt-desc" style="font-weight: 600; color: #132A13;">
                Cara kerja PMT umumnya menggunakan teknik regresi dengan pemeringkatan status sosial ekonomi.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ------------------ BODY 2: 6 KOMBINASI BIG DATA SPASIAL ------------------
    st.markdown('<div class="bigdata-title">Big Data Spasial yang Dapat Dikombinasikan dengan PMT</div>', unsafe_allow_html=True)

    # 6 Kolom Grid
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown("""
            <div class="bigdata-card">
                <div class="bigdata-badge">1</div>
                <div class="bigdata-card-title">Isochrone</div>
                <div class="bigdata-card-desc">Isochrone adalah metode pemetaan yang menggambarkan suatu area terjangkau dari suatu titik dalam batas waktu tertentu.</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="bigdata-card">
                <div class="bigdata-badge">2</div>
                <div class="bigdata-card-title">NTL</div>
                <div class="bigdata-card-desc">Data NTL dapat menggambarkan aktivitas manusia.</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="bigdata-card">
                <div class="bigdata-badge">3</div>
                <div class="bigdata-card-title">LST</div>
                <div class="bigdata-card-desc">Data LST dapat menggambarkan wilayah perkotaan dan pedesaan.</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <div class="bigdata-card">
                <div class="bigdata-badge">4</div>
                <div class="bigdata-card-title">NDVI</div>
                <div class="bigdata-card-desc">Data NDVI dapat menggambarkan wilayah perkotaan dan pedesaan.</div>
            </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""
            <div class="bigdata-card">
                <div class="bigdata-badge">5</div>
                <div class="bigdata-card-title">NDBI</div>
                <div class="bigdata-card-desc">Data NDBI dapat menggambarkan wilayah perkotaan dan pedesaan.</div>
            </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown("""
            <div class="bigdata-card">
                <div class="bigdata-badge">6</div>
                <div class="bigdata-card-title">NDWI</div>
                <div class="bigdata-card-desc">Data NDWI dapat menggambarkan wilayah perkotaan dan pedesaan.</div>
            </div>
        """, unsafe_allow_html=True)

    # Tombol Action Ke Peta Interaktif (Posisi Center Presisi 100%)
    st.markdown("<br>", unsafe_allow_html=True)

    # Gunakan 3 kolom dengan proporsi [1, 2, 1] agar kolom tengah pas berada di posisi pusat
    _, col_center, _ = st.columns([1, 2, 1])


# -----------------------------------------------------------------------------
# HALAMAN: PETA INTERAKTIF
# -----------------------------------------------------------------------------
if st.session_state['current_page'] == "Peta Interaktif":

    st.title("Peta Interaktif")
    st.write(
        "Pilih wilayah yang ingin ditampilkan. "
        "Data spasial akan dimuat setelah tombol filter dijalankan."
    )

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "peta-interaktif")

    shp_path = os.path.join(
        DATA_DIR,
        "shp_lokus_kecamatan.shp"
    )

    ISOCHRONE_FOLDER = {
        "11": "isochrone_aceh",
        "31": "isochrone_jkt",
        "51": "isochrone_bali",
    }

    # ==========================================================
    # 1. LOAD ATRIBUT SHP UNTUK DROPDOWN SAJA
    # ==========================================================

    @st.cache_data
    def load_region_list():

        gdf = gpd.read_file(
            shp_path,
            ignore_geometry=True
        )

        required_cols = [
            "kdprov",
            "kdkab",
            "kdkec",
            "kdwil",
            "nmprov",
            "nmkec",
            "nmkab"
        ]

        missing = [
            col for col in required_cols
            if col not in gdf.columns
        ]

        if missing:
            raise ValueError(
                f"Kolom berikut tidak ditemukan pada shapefile: {missing}"
            )

        df = gdf[required_cols].copy()

        # Jadikan kode sebagai string
        for col in ["kdprov", "kdkab", "kdkec", "kdwil"]:
            df[col] = df[col].astype(str).str.strip()

        # Hilangkan .0 kalau kode terbaca sebagai angka
        for col in ["kdprov", "kdkab", "kdkec", "kdwil"]:
            df[col] = df[col].str.replace(r"\.0$", "", regex=True)

        # Pastikan kode memiliki leading zero jika diperlukan
        df["kdprov"] = df["kdprov"].str.zfill(2)
        df["kdkab"] = df["kdkab"].str.zfill(4)
        df["kdkec"] = df["kdkec"].str.zfill(6)

        return df.drop_duplicates()


    try:
        df_region = load_region_list()

    except Exception as e:
        st.error(f"Gagal membaca daftar wilayah: {e}")
        st.stop()


    # ==========================================================
    # 2. FILTER PROVINSI
    # ==========================================================

    provinsi_list = sorted(
        df_region["kdprov"].unique().tolist()
    )

    selected_kdprov = st.selectbox(
        "Pilih Provinsi",
        options=provinsi_list
    )


    # Filter berdasarkan provinsi
    df_prov = df_region[
        df_region["kdprov"] == selected_kdprov
    ].copy()


    # ==========================================================
    # 3. FILTER KABUPATEN/KOTA
    # ==========================================================

    kab_list = (
        df_prov[["kdkab", "nmkab"]]
        .drop_duplicates()
        .sort_values("nmkab")
    )

    kab_options = {
        f"{row['nmkab']} ({row['kdkab']})": row["kdkab"]
        for _, row in kab_list.iterrows()
    }

    selected_kab_display = st.selectbox(
        "Pilih Kabupaten/Kota",
        options=list(kab_options.keys())
    )

    selected_kdkab = kab_options[selected_kab_display]


    # Filter berdasarkan kabupaten
    df_kab = df_prov[
        df_prov["kdkab"] == selected_kdkab
    ].copy()


    # ==========================================================
    # 4. FILTER KECAMATAN
    # ==========================================================

    kec_list = (
        df_kab[["kdkec", "kdwil", "nmkec"]]
        .drop_duplicates()
        .sort_values("nmkec")
    )

    kec_options = {
        f"{row['nmkec']} ({row['kdkec']})": row["kdwil"]
        for _, row in kec_list.iterrows()
    }

    selected_kec_display = st.selectbox(
        "Pilih Kecamatan",
        options=list(kec_options.keys())
    )

    target_kdwil = kec_options[selected_kec_display]


    # Ambil informasi wilayah terpilih
    selected_row = df_kab[
        df_kab["kdwil"] == target_kdwil
    ].iloc[0]


    # ==========================================================
    # 5. TOMBOL FILTER
    # ==========================================================

    if "filter_submitted" not in st.session_state:
        st.session_state["filter_submitted"] = False

    btn_submit = st.button(
        "Jalankan Filter",
        type="primary"
    )

    if btn_submit:
        st.session_state["filter_submitted"] = True


    # ==========================================================
    # 4. BARU LOAD DATA SPASIAL SETELAH BUTTON DIKLIK
    # ==========================================================

    if st.session_state["filter_submitted"]:

        st.info(
            f"Memuat data spasial untuk "
            f"{selected_row['nmkec']} — {selected_row['nmkab']}..."
        )

        # ======================================================
        # 1. LOAD SHP KECAMATAN TERPILIH
        # ======================================================

        try:

            gdf_kec = gpd.read_file(shp_path)

            gdf_selected = gdf_kec[
                gdf_kec["kdwil"].astype(str).str.strip() == target_kdwil
            ].copy()

            if gdf_selected.empty:
                st.warning(
                    f"Wilayah dengan kdwil = {target_kdwil} "
                    "tidak ditemukan."
                )
                st.stop()

            # Pastikan WGS84
            if gdf_selected.crs is not None:
                gdf_selected = gdf_selected.to_crs(epsg=4326)

        except Exception as e:

            st.error(f"Gagal membaca shapefile: {e}")
            st.stop()


        # ======================================================
        # 2. LOAD ISOCHRONE
        # ======================================================

        kdprov = str(selected_row["kdprov"]).strip()

        iso_folder = ISOCHRONE_FOLDER.get(kdprov)

        gdf_iso = None

        if iso_folder is None:

            st.warning(
                f"Folder isochrone untuk provinsi "
                f"'{selected_row['nmprov']}' belum tersedia di mapping."
            )

        else:

            isochrone_path = os.path.join(
                DATA_DIR,
                iso_folder,
                f"isochrone_{target_kdwil}.geojson"
            )

            if os.path.exists(isochrone_path):

                try:

                    gdf_iso = gpd.read_file(
                        isochrone_path
                    )

                    if gdf_iso.crs is not None:
                        gdf_iso = gdf_iso.to_crs(
                            epsg=4326
                        )

                except Exception as e:

                    st.warning(
                        f"Isochrone ditemukan tetapi "
                        f"gagal dibaca: {e}"
                    )

            else:

                st.warning(
                    f"File isochrone tidak ditemukan.\n\n"
                    f"Path yang dicari:\n"
                    f"{isochrone_path}"
                )


        # ======================================================
        # 3. LOAD AMENITY
        # ======================================================

        amenity_path = os.path.join(
            DATA_DIR,
            "amenity_lokus_geometri.csv"
        )

        df_amenity = None

        if os.path.exists(amenity_path):

            try:

                df_amenity = pd.read_csv(
                    amenity_path,
                    low_memory=False
                )

                # Pastikan koordinat numerik
                df_amenity["xcoord"] = pd.to_numeric(
                    df_amenity["xcoord"],
                    errors="coerce"
                )

                df_amenity["ycoord"] = pd.to_numeric(
                    df_amenity["ycoord"],
                    errors="coerce"
                )

                # Buang data dengan koordinat kosong
                df_amenity = df_amenity.dropna(
                    subset=["xcoord", "ycoord"]
                ).copy()

            except Exception as e:

                st.warning(
                    f"Gagal membaca data amenity: {e}"
                )

        else:

            st.warning(
                "File amenity_jakarta_geom.csv tidak ditemukan."
            )

        # ======================================================
        # 4. FILTER AMENITY BERDASARKAN KECAMATAN
        # ======================================================

        gdf_amenity_selected = None

        if df_amenity is not None and not df_amenity.empty:

            # Ubah data amenity menjadi GeoDataFrame
            gdf_amenity = gpd.GeoDataFrame(
                df_amenity,
                geometry=gpd.points_from_xy(
                    df_amenity["xcoord"],
                    df_amenity["ycoord"]
                ),
                crs="EPSG:4326"
            )

            # Samakan CRS dengan SHP kecamatan
            if gdf_selected.crs != gdf_amenity.crs:
                gdf_amenity = gdf_amenity.to_crs(
                    gdf_selected.crs
                )

            # Spatial join:
            # hanya titik yang berada di dalam kecamatan terpilih
            gdf_amenity_selected = gpd.sjoin(
                gdf_amenity,
                gdf_selected[["geometry"]],
                how="inner",
                predicate="within"
            )

            st.write(
                f"Jumlah amenity pada kecamatan terpilih: "
                f"{len(gdf_amenity_selected)}"
            )

        # ======================================================
        # 5. FILTER TIPE AMENITY
        # ======================================================

        gdf_amenity_filtered = None

        amenity_icons = {
            "kindergarten": "bi-backpack-fill",
            "school": "bi-book-half",
            "university": "bi-mortarboard-fill",
            "fuel": "bi-ev-station-fill",
            "atm": "bi-credit-card",
            "bank": "bi-bank2",
            "clinic": "bi-hospital",
            "dentist": "bi-hospital",
            "doctors": "bi-hospital",
            "hospital": "bi-hospital",
            "pharmacy": "bi-capsule-pill",
            "fire_station": "bi-fire",
            "police": "bi-shield-shaded",
            "marketplace": "bi-cart-check-fill",
            "place_of_worship": "bi-bookmark-heart-fill"
        }

        if (
            gdf_amenity_selected is not None
            and not gdf_amenity_selected.empty
        ):

            st.markdown("### Filter Amenity")

            amenity_keyword = st.text_input(
                "Masukkan keyword amenity",
                placeholder="Contoh: school, hospital, restaurant",
                help="Pisahkan beberapa keyword dengan koma."
            )

            if amenity_keyword.strip():

                keywords = [
                    x.strip().lower()
                    for x in amenity_keyword.split(",")
                    if x.strip()
                ]

                pattern = "|".join(
                    [k.replace(".", r"\.") for k in keywords]
                )

                mask = (
                    gdf_amenity_selected["amenity"]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        pattern,
                        regex=True,
                        na=False
                    )
                )

                gdf_amenity_filtered = (
                    gdf_amenity_selected[mask].copy()
                )

            else:

                gdf_amenity_filtered = (
                    gdf_amenity_selected.copy()
                )

            st.caption(
                f"{len(gdf_amenity_filtered)} amenity ditampilkan"
            )

        # ======================================================
        # 4. BUAT PETA (m)
        # ======================================================

        centroid = gdf_selected.geometry.union_all().centroid

        m = folium.Map(
            location=[
                centroid.y,
                centroid.x
            ],
            zoom_start=14,
            tiles="OpenStreetMap"
        )


        # ======================================================
        # 5. SHP KECAMATAN
        # ======================================================

        folium.GeoJson(
            gdf_selected.__geo_interface__,
            name="Wilayah Kecamatan",

            style_function=lambda feature: {
                "fillColor": "#3186cc",
                "color": "#1f4e79",
                "weight": 2,
                "fillOpacity": 0.20
            },

            tooltip=folium.GeoJsonTooltip(
                fields=["nmkec", "nmkab"],
                aliases=[
                    "Kecamatan",
                    "Kabupaten/Kota"
                ]
            )
        ).add_to(m)


        # ======================================================
        # 6. ISOCHRONE
        # ======================================================

        if gdf_iso is not None and not gdf_iso.empty:

            folium.GeoJson(
                gdf_iso.__geo_interface__,
                name="Isochrone",

                style_function=lambda feature: {
                    "fillColor": "#ff7800",
                    "color": "#ff7800",
                    "weight": 2,
                    "fillOpacity": 0.25
                },

                tooltip="Isochrone"
            ).add_to(m)

        # ======================================================
        # 7. AMENITY HASIL FILTER
        # ======================================================

        # ======================================================
        # 9. AMENITY DENGAN BOOTSTRAP ICON
        # ======================================================

        if (
            gdf_amenity_filtered is not None
            and not gdf_amenity_filtered.empty
        ):

            # Bootstrap Icons dimasukkan ke dalam map Folium
            from branca.element import Element

            bootstrap_icons_css = """
            <link rel="stylesheet"
                href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
            """

            m.get_root().header.add_child(
                Element(bootstrap_icons_css)
            )

            # CSS marker
            marker_css = """
            <style>

            .amenity-marker {
                width: 34px;
                height: 34px;
                border-radius: 50%;

                background-color: #132A13;
                color: #ECF39E;

                display: flex;
                align-items: center;
                justify-content: center;

                font-size: 17px;

                border: 2px solid #FFFCF2;

                box-shadow:
                    0 2px 6px rgba(0, 0, 0, 0.3);
            }

            .amenity-marker i {
                line-height: 1;
            }

            </style>
            """

            m.get_root().header.add_child(
                Element(marker_css)
            )

            # Marker cluster
            marker_cluster = MarkerCluster(
                name="Amenity"
            )

            marker_cluster.add_to(m)

            # Tambahkan marker
            for _, row in gdf_amenity_filtered.iterrows():

                amenity_type = str(
                    row["amenity"]
                ).strip().lower()

                # Ambil icon berdasarkan tipe amenity
                # Kalau tidak ada → gunakan geo-alt
                icon_name = amenity_icons.get(
                    amenity_type,
                    "bi-geo-alt-fill"
                )

                # Popup
                popup_text = ""

                if "name" in gdf_amenity_filtered.columns:
                    if pd.notna(row["name"]):
                        popup_text += (
                            f"<b>{row['name']}</b><br>"
                        )

                if "amenity" in gdf_amenity_filtered.columns:
                    if pd.notna(row["amenity"]):
                        popup_text += (
                            f"Amenity: {row['amenity']}<br>"
                        )

                if "addr:full" in gdf_amenity_filtered.columns:
                    if pd.notna(row["addr:full"]):
                        popup_text += (
                            f"Alamat: {row['addr:full']}"
                        )

                # HTML Bootstrap Icon
                icon_html = f"""
                <div class="amenity-marker">
                    <i class="bi {icon_name}"></i>
                </div>
                """

                icon = folium.DivIcon(
                    html=icon_html,
                    icon_size=(34, 34),
                    icon_anchor=(17, 17)
                )

                folium.Marker(
                    location=[
                        row.geometry.y,
                        row.geometry.x
                    ],
                    popup=folium.Popup(
                        popup_text,
                        max_width=300
                    ),
                    icon=icon
                ).add_to(marker_cluster)

        # ======================================================
        # 8. LAYER CONTROL
        # ======================================================

        folium.LayerControl().add_to(m)


        # ======================================================
        # 9. TAMPILKAN PETA
        # ======================================================

        st.success(
            f"Peta berhasil dimuat untuk "
            f"{selected_row['nmkec']} — "
            f"{selected_row['nmkab']}"
        )

        st_folium(
            m,
            width="100%",
            height=650,
            returned_objects=[]
        )

# =============================================================================
# FOOTER (Sesuai Pedoman)
# =============================================================================
st.markdown("""
    <div class="custom-footer">
        <div class="footer-author">Made by Zahra Mufidah Ariani</div>
        <div>Copyright © 2026 | 222212932</div>
    </div>
""", unsafe_allow_html=True)