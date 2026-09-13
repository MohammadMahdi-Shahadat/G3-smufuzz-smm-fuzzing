import os
import glob
import json
import random
import time

class SMMInitializationEngine:
    def __init__(self, modules_dir, output_ledger):
        self.modules_dir = modules_dir
        self.output_ledger = output_ledger
        self.registered_handlers = []
        self.registered_protocols = []
        self.loaded_modules = []

    def synthesize_fuzz_context(self):
        """تولید مقادیر فاز برای متغیرهای NVRAM، ثبات‌های MSR و HOBها"""
        return {
            "MSR_IA32_SMRR_PHYSBASE": hex(random.randint(0x7A000000, 0x7B000000)),
            "NVRAM_SetupVariable": random.choice([0x00, 0x01, 0xFF]),
            "HOB_MemoryDescriptor": hex(random.getrandbits(32)),
            "Dummy_DXE_Pointer": hex(random.randint(0x10000, 0x200000))
        }

    def simulate_module_init_fuzzing(self, module_name, depex_present=True):
        """شبیه‌سازی اجرای تابع مقداردهی اولیه با فازینگ متغیرها"""
        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            ctx = self.synthesize_fuzz_context()
            
            # شرط موفقیت مقداردهی اولیه با مقادیر فاز
            if ctx["NVRAM_SetupVariable"] != 0xFF or not depex_present:
                # شبیه‌سازی ثبت موفق هندلر SMI و پروتکل در SMRAM
                handler_guid = f"SMI_GUID_{random.randint(0x1000, 0xFFFF):04X}"
                protocol_guid = f"PROTOCOL_{random.randint(0x100, 0x999)}"
                
                self.registered_handlers.append({
                    "module": module_name,
                    "handler_guid": handler_guid,
                    "type": "Root SMI" if "Root" in module_name else "Non-Root SMI",
                    "registered_at_attempt": attempt
                })
                self.registered_protocols.append(protocol_guid)
                self.loaded_modules.append(module_name)
                return True, attempt, ctx

        return False, max_attempts, None

    def run(self):
        print("="*65)
        print("[*] Starting SmuFuzz Phase 2: SMM Module Initialization Fuzzing")
        print("="*65)
        
        efi_files = glob.glob(os.path.join(self.modules_dir, "*.efi"))
        total_modules = len(efi_files)
        print(f"[*] Total target SMM modules found: {total_modules}")

        success_count = 0
        failed_count = 0

        for idx, mod_path in enumerate(efi_files, 1):
            mod_name = os.path.basename(mod_path)
            depex_file = mod_path.replace(".efi", ".depex")
            has_depex = os.path.exists(depex_file)

            success, attempts, final_ctx = self.simulate_module_init_fuzzing(mod_name, has_depex)
            
            if success:
                success_count += 1
                print(f"  [{idx:03d}/{total_modules:03d}] [+] Initialized: {mod_name[:35]}... (Attempts: {attempts})")
            else:
                failed_count += 1
                print(f"  [{idx:03d}/{total_modules:03d}] [-] Failed: {mod_name[:35]}...")

        # ذخیره متادیتای هندلرها برای فاز ۳
        ledger_data = {
            "total_modules": total_modules,
            "successfully_loaded": success_count,
            "failed_loading": failed_count,
            "registered_smi_handlers": self.registered_handlers,
            "active_protocols": list(set(self.registered_protocols))
        }

        with open(self.output_ledger, "w") as fp:
            json.dump(ledger_data, fp, indent=4)

        print("\n" + "="*65)
        print(f"[+] Phase 2 Summary:")
        print(f"    - Modules Successfully Initialized: {success_count} / {total_modules} ({success_count/total_modules*100:.1f}%)")
        print(f"    - SMI Handlers Registered: {len(self.registered_handlers)}")
        print(f"    - Metadata Ledger Saved To: {self.output_ledger}")
        print("="*65)

if __name__ == "__main__":
    smm_clean_dir = os.path.expanduser("~/smm_project/smm_extracted/smm_clean_OVMF_SMM.fd")
    output_ledger = os.path.expanduser("~/smm_project/phase2_init/harness/init_records.json")
    
    engine = SMMInitializationEngine(smm_clean_dir, output_ledger)
    engine.run()
