#!/usr/bin/env python3
"""
GTA San Andreas (Xbox 360) — TOC to SZ Converter
Converts .toc files to .sz files for texture database compatibility.

Formula (verified against all original game files):
  - Magic (first 4 bytes) = total archive data size (same in both .toc and .sz)
  - Each entry: SZ = next_TOC_offset - current_TOC_offset - 12
  - Last entry: SZ = magic - current_TOC_offset - 12  
  - FFFFFFFF entries are preserved as-is

Usage: Run this script, select one or more .toc files, and .sz files will be
generated in the same directory.
"""

import struct
import os
import sys

# ── Core Converter ──────────────────────────────────────────────────────────

def convert_toc_to_sz(toc_path):
    """Convert a .toc file to .sz. Returns (output_path, stats_dict) or raises."""
    with open(toc_path, 'rb') as f:
        toc_data = f.read()

    if len(toc_data) < 8:
        raise ValueError(f"File too small ({len(toc_data)} bytes)")

    # Parse
    magic = struct.unpack_from('>I', toc_data, 0)[0]
    num_entries = (len(toc_data) - 4) // 4
    toc_vals = [struct.unpack_from('>I', toc_data, 4 + i * 4)[0] for i in range(num_entries)]

    # Build SZ
    sz_data = bytearray(struct.pack('>I', magic))  # Same magic
    valid = 0
    empty = 0

    for i in range(num_entries):
        if toc_vals[i] == 0xFFFFFFFF:
            sz_data += struct.pack('>I', 0xFFFFFFFF)
            empty += 1
            continue

        valid += 1

        # Find next valid offset (or use magic as the end-of-archive marker)
        next_offset = None
        for j in range(i + 1, num_entries):
            if toc_vals[j] != 0xFFFFFFFF:
                next_offset = toc_vals[j]
                break

        if next_offset is None:
            # Last valid entry — use magic (total archive size) as the boundary
            sz_val = magic - toc_vals[i] - 12
        else:
            sz_val = next_offset - toc_vals[i] - 12

        sz_data += struct.pack('>I', max(0, sz_val))

    # Write output
    # .toc → .sz (handle both "name.360.toc" and "name.toc")
    base = toc_path
    if base.lower().endswith('.toc'):
        out_path = base[:-4] + '.sz'
    else:
        out_path = base + '.sz'

    with open(out_path, 'wb') as f:
        f.write(sz_data)

    stats = {
        'input': os.path.basename(toc_path),
        'output': os.path.basename(out_path),
        'output_path': out_path,
        'magic': magic,
        'total_entries': num_entries,
        'valid_entries': valid,
        'empty_entries': empty,
        'file_size': len(sz_data),
    }
    return out_path, stats


# ── GUI ─────────────────────────────────────────────────────────────────────

def run_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.title("GTA SA Xbox 360 — TOC → SZ Converter")
    root.configure(bg='#1a1a2e')
    root.resizable(True, True)

    # Try to set a reasonable size
    root.geometry("620x520")
    root.minsize(500, 400)

    # ── Styles ──
    BG = '#1a1a2e'
    BG2 = '#16213e'
    FG = '#e0e0e0'
    ACCENT = '#ff6b35'
    GREEN = '#35ff6b'
    MONO = ('Consolas', 9) if sys.platform == 'win32' else ('Courier', 10)
    FONT = ('Segoe UI', 10) if sys.platform == 'win32' else ('Helvetica', 10)
    FONT_BOLD = ('Segoe UI', 10, 'bold') if sys.platform == 'win32' else ('Helvetica', 10, 'bold')
    FONT_TITLE = ('Segoe UI', 14, 'bold') if sys.platform == 'win32' else ('Helvetica', 14, 'bold')

    # ── Title ──
    title_frame = tk.Frame(root, bg=BG, pady=12)
    title_frame.pack(fill='x')

    tk.Label(title_frame, text="TOC → SZ Converter", font=FONT_TITLE,
             fg=ACCENT, bg=BG).pack()
    tk.Label(title_frame, text="GTA San Andreas · Xbox 360 · Regenerate .sz after modding",
             font=('Segoe UI', 8) if sys.platform == 'win32' else ('Helvetica', 8),
             fg='#666', bg=BG).pack()

    # ── Buttons ──
    btn_frame = tk.Frame(root, bg=BG, pady=8)
    btn_frame.pack(fill='x', padx=20)

    def select_files():
        paths = filedialog.askopenfilenames(
            title="Select .toc files",
            filetypes=[("TOC files", "*.toc"), ("All files", "*.*")]
        )
        if paths:
            process_files(list(paths))

    def select_folder():
        folder = filedialog.askdirectory(title="Select folder containing .toc files")
        if folder:
            toc_files = []
            for f in os.listdir(folder):
                if f.lower().endswith('.toc'):
                    toc_files.append(os.path.join(folder, f))
            if toc_files:
                process_files(sorted(toc_files))
            else:
                log_text.insert('end', "No .toc files found in that folder.\n\n", 'warn')

    select_btn = tk.Button(btn_frame, text="📂  Select .toc Files",
                           command=select_files, font=FONT_BOLD,
                           bg=ACCENT, fg='white', activebackground='#e55a28',
                           activeforeground='white', relief='flat',
                           padx=16, pady=6, cursor='hand2')
    select_btn.pack(side='left', padx=(0, 8))

    folder_btn = tk.Button(btn_frame, text="📁  Convert Entire Folder",
                           command=select_folder, font=FONT,
                           bg=BG2, fg=FG, activebackground='#1e2d4d',
                           activeforeground='white', relief='flat',
                           padx=16, pady=6, cursor='hand2')
    folder_btn.pack(side='left')

    # ── Log area ──
    log_frame = tk.Frame(root, bg=BG, padx=20, pady=8)
    log_frame.pack(fill='both', expand=True)

    log_text = tk.Text(log_frame, bg='#0d1117', fg=FG, font=MONO,
                       relief='flat', padx=12, pady=10, wrap='word',
                       insertbackground=FG, selectbackground='#264f78',
                       borderwidth=0, highlightthickness=1,
                       highlightbackground='#333', highlightcolor=ACCENT)
    log_text.pack(fill='both', expand=True)

    scrollbar = tk.Scrollbar(log_text, command=log_text.yview)
    scrollbar.pack(side='right', fill='y')
    log_text.configure(yscrollcommand=scrollbar.set)

    # Tags for colored text
    log_text.tag_configure('header', foreground=ACCENT, font=FONT_BOLD)
    log_text.tag_configure('success', foreground=GREEN)
    log_text.tag_configure('error', foreground='#ff4444')
    log_text.tag_configure('warn', foreground='#ffb835')
    log_text.tag_configure('dim', foreground='#666')
    log_text.tag_configure('info', foreground='#88aacc')

    # Welcome message
    log_text.insert('end', "Ready to convert.\n\n", 'dim')
    log_text.insert('end', "Select one or more .toc files, or an entire folder.\n", 'dim')
    log_text.insert('end', "A matching .sz file will be generated next to each .toc.\n\n", 'dim')
    log_text.insert('end', "Formula: SZ[i] = next_offset - offset - 12\n", 'info')
    log_text.insert('end', "         SZ[last] = archive_size - offset - 12\n\n", 'info')

    def process_files(paths):
        log_text.insert('end', f"{'─' * 50}\n", 'dim')
        log_text.insert('end', f"Converting {len(paths)} file(s)...\n\n", 'header')

        success_count = 0
        fail_count = 0

        for path in paths:
            fname = os.path.basename(path)
            try:
                out_path, stats = convert_toc_to_sz(path)
                success_count += 1

                log_text.insert('end', f"  ✓ {fname}\n", 'success')
                log_text.insert('end', f"    → {stats['output']}\n", 'dim')
                log_text.insert('end', f"    {stats['valid_entries']} entries, "
                                       f"{stats['empty_entries']} empty, "
                                       f"{stats['file_size']} bytes\n", 'dim')
                log_text.insert('end', f"    Archive size: {stats['magic']:,}\n\n", 'dim')

            except Exception as e:
                fail_count += 1
                log_text.insert('end', f"  ✗ {fname}\n", 'error')
                log_text.insert('end', f"    Error: {e}\n\n", 'error')

        # Summary
        if success_count > 0 and fail_count == 0:
            log_text.insert('end', f"Done — all {success_count} file(s) converted successfully.\n\n", 'success')
        elif success_count > 0:
            log_text.insert('end', f"Done — {success_count} converted, {fail_count} failed.\n\n", 'warn')
        else:
            log_text.insert('end', f"Failed — no files converted.\n\n", 'error')

        log_text.see('end')

    root.mainloop()


# ── CLI fallback ────────────────────────────────────────────────────────────

def run_cli(paths):
    print("GTA SA Xbox 360 — TOC to SZ Converter")
    print("=" * 40)
    for path in paths:
        try:
            out_path, stats = convert_toc_to_sz(path)
            print(f"  ✓ {stats['input']} → {stats['output']}")
            print(f"    {stats['valid_entries']} entries, archive size: {stats['magic']:,}")
        except Exception as e:
            print(f"  ✗ {os.path.basename(path)}: {e}")
    print("\nDone.")


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # CLI mode: pass .toc files as arguments
        run_cli(sys.argv[1:])
    else:
        # GUI mode
        try:
            run_gui()
        except ImportError:
            print("tkinter not available. Use CLI mode:")
            print(f"  python {sys.argv[0]} file1.toc file2.toc ...")
            sys.exit(1)
