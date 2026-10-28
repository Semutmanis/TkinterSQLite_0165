import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

DB_NAME = "prediksi_diabetes.db"

# Warna label hasil: (warna latar, warna teks)
WARNA = {
    "Rendah": ("green", "white"),
    "Waspada": ("yellow", "black"),
    "Sedang": ("orange", "black"),
    "Tinggi": ("red", "white"),
    "Sangat Tinggi": ("dark red", "white"),
}


# ---------- Database ----------
def run_query(sql, params=()):
    conn = sqlite3.connect(DB_NAME)
    try:
        with conn:
            return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def init_db():
    run_query("""CREATE TABLE IF NOT EXISTS pasien (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_pasien TEXT NOT NULL,
        usia INTEGER NOT NULL,
        gula_darah REAL NOT NULL,
        bmi REAL NOT NULL,
        riwayat_ortu TEXT NOT NULL,
        hasil_prediksi TEXT NOT NULL)""")


def add_pasien(nama, usia, gula, bmi, riwayat, hasil):
    run_query("INSERT INTO pasien (nama_pasien, usia, gula_darah, bmi, "
              "riwayat_ortu, hasil_prediksi) VALUES (?, ?, ?, ?, ?, ?)",
              (nama, usia, gula, bmi, riwayat, hasil))


def get_pasien():
    return run_query("SELECT id, nama_pasien, usia, gula_darah, bmi, "
                     "riwayat_ortu, hasil_prediksi FROM pasien ORDER BY id")


def delete_pasien(pid):
    run_query("DELETE FROM pasien WHERE id = ?", (pid,))


# ---------- Logika prediksi ----------
def prediksi_risiko(gula, bmi, riwayat):
    ada_riwayat = (riwayat == "Ya")

    if gula >= 200:
        # Tinggi atau Sangat Tinggi
        if bmi >= 30 or ada_riwayat:
            return "Sangat Tinggi"
        return "Tinggi"

    if gula >= 140:
        # Sedang atau Tinggi, bergantung BMI dan riwayat orang tua
        if bmi >= 30 or ada_riwayat:
            return "Tinggi"
        return "Sedang"

    # gula < 140
    if bmi >= 30:
        # Waspada atau Sedang
        if ada_riwayat:
            return "Sedang"
        return "Waspada"
    if ada_riwayat:
        return "Waspada"
    return "Rendah"


init_db()
root = tk.Tk()
root.title("Prediksi Risiko Diabetes")

# ---------- Form ----------
entries = {}
for i, field in enumerate(["Nama Pasien", "Usia", "Gula Darah (mg/dL)", "BMI"]):
    tk.Label(root, text=field).grid(row=i, column=0, sticky="w", padx=6)
    entries[field] = tk.Entry(root, width=30)
    entries[field].grid(row=i, column=1, pady=4)

tk.Label(root, text="Riwayat Diabetes Ortu").grid(row=4, column=0,
                                                  sticky="w", padx=6)
cb_riwayat = ttk.Combobox(root, values=["Ya", "Tidak"], state="readonly",
                          width=27)
cb_riwayat.grid(row=4, column=1, pady=4)

# Label hasil prediksi
lbl_hasil = tk.Label(root, text="Hasil prediksi: -", width=40, pady=6)
lbl_hasil.grid(row=6, column=0, columnspan=2, pady=4)

# Tabel
cols = ("id", "nama", "usia", "gula", "bmi", "riwayat", "hasil")
tree = ttk.Treeview(root, columns=cols, show="headings", height=8)
for c in cols:
    tree.heading(c, text=c.title())
    tree.column(c, width=90, anchor="center")
tree.column("nama", width=130, anchor="center")
tree.column("id", width=40, anchor="center")
tree.grid(row=7, column=0, columnspan=2, padx=6, pady=6)


# ---------- Fungsi ----------
def read_form():
    nama = entries["Nama Pasien"].get().strip()
    usia = entries["Usia"].get().strip()
    gula = entries["Gula Darah (mg/dL)"].get().strip().replace(",", ".")
    bmi = entries["BMI"].get().strip().replace(",", ".")
    riwayat = cb_riwayat.get()

    if not nama or not usia or not gula or not bmi or not riwayat:
        messagebox.showwarning("Missing data", "Semua kolom wajib diisi.")
        return None
    if not nama.replace(" ", "").isalpha():
        messagebox.showwarning("Invalid nama", "Nama hanya boleh huruf.")
        return None
    if not usia.isdigit() or not (1 <= int(usia) <= 120):
        messagebox.showwarning("Invalid usia",
                               "Usia harus angka bulat 1 - 120.")
        return None
    try:
        gula = float(gula)
        bmi = float(bmi)
    except ValueError:
        messagebox.showwarning("Invalid input",
                               "Gula darah dan BMI harus berupa angka.")
        return None
    if not (20 <= gula <= 600):
        messagebox.showwarning("Invalid gula darah",
                               "Gula darah harus antara 20 - 600 mg/dL.")
        return None
    if not (10 <= bmi <= 60):
        messagebox.showwarning("Invalid BMI", "BMI harus antara 10 - 60.")
        return None
    return nama, int(usia), gula, bmi, riwayat


def clear_form():
    for e in entries.values():
        e.delete(0, tk.END)
    cb_riwayat.set("")


def refresh():
    tree.delete(*tree.get_children())
    for row in get_pasien():
        tree.insert("", tk.END, values=row)


def on_prediksi():
    data = read_form()
    if data:
        nama, usia, gula, bmi, riwayat = data
        hasil = prediksi_risiko(gula, bmi, riwayat)
        add_pasien(nama, usia, gula, bmi, riwayat, hasil)
        bg, fg = WARNA[hasil]
        lbl_hasil.config(text=f"Risiko {hasil}", bg=bg, fg=fg)
        clear_form()


def on_lihat():
    refresh()


def on_delete():
    sel = tree.selection()
    if not sel:
        messagebox.showinfo("Delete", "Pilih data di tabel dulu.")
        return
    pid = tree.item(sel[0], "values")[0]
    if messagebox.askyesno("Confirm", "Hapus data pasien ini?"):
        delete_pasien(int(pid))
        refresh()


# ---------- Tombol ----------
btns = tk.Frame(root)
btns.grid(row=5, column=0, columnspan=2, pady=4)
for text, cmd in [("Prediksi", on_prediksi), ("Lihat Data", on_lihat),
                  ("Delete", on_delete), ("Clear", clear_form)]:
    tk.Button(btns, text=text, width=10, command=cmd).pack(side="left", padx=4)

root.mainloop()