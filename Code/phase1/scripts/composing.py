import os
import sys
import shutil

def parse_and_extract_smm(fw_path, base_out_dir):
    fw_name = os.path.basename(fw_path)
    dump_dir = fw_path + ".dump"
    
    out_dir = os.path.join(base_out_dir, f"smm_clean_{fw_name}")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[*] Scanning dump tree: {dump_dir}")
    
    extracted_smm = 0
    extracted_depex = 0
    excluded_count = 0

    for root, dirs, files in os.walk(dump_dir):
        # حذف ماژول‌های مرتبط با PiSmmCpu طبق معماری فاز ۱
        if "PiSmmCpu" in root:
            excluded_count += 1
            continue

        for f in files:
            file_path = os.path.join(root, f)
            
            # ۱. بررسی فایل‌های اجرایی PE32 از روی Magic Header یا ساختار پوشه
            if "PE32" in root or "TE image" in root or f.endswith(".pe") or f.endswith(".efi") or f == "body.bin":
                try:
                    with open(file_path, "rb") as fp:
                        header = fp.read(2)
                        if header == b"MZ":
                            # ساخت یک نام معنادار بر اساس پوشه والد FFS
                            parent_dir_name = os.path.basename(root).replace(" ", "_")
                            module_dir_name = os.path.basename(os.path.dirname(root)).replace(" ", "_")
                            dest_name = f"{module_dir_name}_{parent_dir_name}_{extracted_smm}.efi"
                            shutil.copy(file_path, os.path.join(out_dir, dest_name))
                            extracted_smm += 1
                except Exception:
                    pass

            # ۲. بررسی و استخراج سکشن‌های وابستگی Depex
            if "dependency" in root.lower() or "depex" in root.lower() or "depex" in f.lower():
                if f == "body.bin" or f.endswith(".depex") or f.endswith(".raw"):
                    parent_dir_name = os.path.basename(root).replace(" ", "_")
                    dest_name = f"{parent_dir_name}_{extracted_depex}.depex"
                    shutil.copy(file_path, os.path.join(out_dir, dest_name))
                    extracted_depex += 1

    print("\n" + "="*60)
    print(f"[+] Extraction Summary for {fw_name}:")
    print(f"    - Valid SMM PE Executables: {extracted_smm}")
    print(f"    - Depex Dependency Sections: {extracted_depex}")
    print(f"    - Excluded Low-level Items (PiSmmCpu): {excluded_count}")
    print(f"    - Output Directory: {out_dir}")
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 composing.py <path_to_firmware>")
        sys.exit(1)
    parse_and_extract_smm(sys.argv[1], os.path.expanduser("~/smm_project/smm_extracted"))
