import json
import os

def group_smi_handlers(ledger_path, output_groups_path):
    print("[*] Analyzing handler dependencies and constructing Fuzzing Groups...")
    
    with open(ledger_path, "r") as fp:
        data = json.load(fp)

    handlers = data.get("registered_smi_handlers", [])
    
    # گروه‌بندی بر مبنای ماژول‌های پایه و پیشوندهای سرویس
    groups = {}
    for h in handlers:
        mod = h["module"]
        # استخراج نام دسته‌بندی ماژول
        category = mod.split("_")[1] if "_" in mod else "Core"
        
        if category not in groups:
            groups[category] = []
        groups[category].append(h)

    print("\n" + "="*60)
    print(f"[+] Dependency Grouping Results:")
    print(f"    - Total Identified SMI Groups: {len(groups)}")
    for cat, members in list(groups.items())[:8]:
        print(f"    -> Group [{cat:<15}]: {len(members)} handlers")
    print("    ... (and more)")
    print("="*60)

    with open(output_groups_path, "w") as fp:
        json.dump(groups, fp, indent=4)
    print(f"[+] Grouped metadata saved to: {output_groups_path}")

if __name__ == "__main__":
    ledger_file = os.path.expanduser("~/smm_project/phase2_init/harness/init_records.json")
    groups_file = os.path.expanduser("~/smm_project/phase2_init/harness/fuzz_groups.json")
    group_smi_handlers(ledger_file, groups_file)
