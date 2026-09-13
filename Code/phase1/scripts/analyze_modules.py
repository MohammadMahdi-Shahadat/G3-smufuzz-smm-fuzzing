import os
import glob

smm_dir = os.path.expanduser("~/smm_project/smm_extracted/smm_modules_OVMF_SMM.fd")
extracted_files = glob.glob(os.path.join(smm_dir, "*"))

pe_files = [f for f in extracted_files if f.endswith(".pe") or f.endswith(".efi")]
bin_files = [f for f in extracted_files if f.endswith(".bin")]

print("="*60)
print(f"[*] SMM Extraction Analysis Report:")
print(f"    - Total Extracted Items: {len(extracted_files)}")
print(f"    - Executable PE/EFI Images: {len(pe_files)}")
print(f"    - Raw Section / Data Binaries: {len(bin_files)}")
print("="*60)

print("\n[*] Sample Extracted SMM Executables:")
for pe in pe_files[:10]:
    print(f"  -> {os.path.basename(pe)}")
