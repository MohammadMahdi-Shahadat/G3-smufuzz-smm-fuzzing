import os
import glob
import shutil

smm_dir = os.path.expanduser("~/smm_project/smm_extracted/smm_modules_OVMF_SMM.fd")
verified_pe_dir = os.path.join(smm_dir, "pe_images")
os.makedirs(verified_pe_dir, exist_ok=True)

files = glob.glob(os.path.join(smm_dir, "*"))

pe_count = 0
depex_count = 0

print("[*] Inspecting binaries for PE (MZ) headers and Depex sections...")

for f in files:
    if os.path.isdir(f):
        continue
    with open(f, "rb") as fp:
        header = fp.read(4)
        if len(header) >= 2 and header[:2] == b"MZ":
            pe_count += 1
            dest_name = os.path.basename(f) + ".efi"
            shutil.copy(f, os.path.join(verified_pe_dir, dest_name))
        elif "DEPEX" in f.upper() or "DXE_DEPEX" in f.upper():
            depex_count += 1

print("="*60)
print(f"[+] Validation Summary:")
print(f"    - Valid SMM PE/EFI Executables Identified: {pe_count}")
print(f"    - Depex/Dependency Sections: {depex_count}")
print(f"    - Clean PE Directory: {verified_pe_dir}")
print("="*60)

pe_files = os.listdir(verified_pe_dir)
print(f"\n[*] Extracted SMM Drivers (Showing first 10):")
for p in pe_files[:10]:
    print(f"  [+] {p}")
