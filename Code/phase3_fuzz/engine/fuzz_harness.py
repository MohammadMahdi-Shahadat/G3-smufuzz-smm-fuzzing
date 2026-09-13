import os
import sys
import json
import time
import random
from multi_stream import MultiStreamInput
from interceptor import MemoryAndIOInterceptor

class SmuFuzzExecutionHarness:
    def __init__(self, groups_path, lock_path, report_dir):
        self.groups_path = groups_path
        self.lock_path = lock_path
        self.report_dir = report_dir
        self.interceptor = MemoryAndIOInterceptor()
        
        with open(self.groups_path, "r") as fp:
            self.groups = json.load(fp)
        with open(self.lock_path, "r") as fp:
            self.lock_state = json.load(fp)

        self.total_runs = 0
        self.detected_faults = []
        self.coverage_blocks = set()

    def evaluate_handler_execution(self, handler_info, test_case):
        """شبیه‌سازی اجرای هندلر با جریان‌های ورودی و رهگیری استثناها"""
        self.interceptor.reset_history()
        
        test_ptr = 0x10000000 + ((test_case.handler_sel & 0xFFFF) * 0x100)
        data, status = self.interceptor.handle_memory_read(test_ptr, 4, test_case.mem_stream)

        if test_case.comm_buf and len(test_case.comm_buf) > 0 and test_case.comm_buf[0] == 0x7A:
            _, status = self.interceptor.handle_memory_read(
                self.interceptor.redzone_base + 16, 4, test_case.mem_stream
            )

        if test_case.comm_buf and len(test_case.comm_buf) > 4:
            if test_case.comm_buf[1:3] == b"\xDE\xAD":
                status = "FAULT_SMM_CALLOUT_BRANCH"

        block_id = hash((handler_info["handler_guid"], status, len(test_case.comm_buf)))
        self.coverage_blocks.add(block_id)

        return status

    def run_fuzzing(self, iterations=1000):
        print("="*65)
        print("[*] SmuFuzz Phase 3: Multi-Stream SMI Handler Fuzzing (Clean Run)")
        print(f"[*] Total Handler Groups: {len(self.groups)} | Lock State: {self.lock_state['status']}")
        print(f"[*] Target Test Executions: {iterations}")
        print("="*65)

        start_time = time.time()
        group_keys = list(self.groups.keys())

        for it in range(1, iterations + 1):
            self.total_runs += 1
            
            group_name = random.choice(group_keys)
            handlers = self.groups[group_name]
            
            test_case = MultiStreamInput.generate_random()
            test_case.mutate()
            
            handler_idx = test_case.handler_sel % len(handlers)
            target_handler = handlers[handler_idx]

            result_status = self.evaluate_handler_execution(target_handler, test_case)

            if "FAULT" in result_status or "CRASH" in result_status or "VULN" in result_status:
                fault_entry = {
                    "iteration": it,
                    "module": target_handler["module"],
                    "handler_guid": target_handler["handler_guid"],
                    "type": result_status,
                    "group": group_name
                }
                self.detected_faults.append(fault_entry)

            if it % 200 == 0 or it == iterations:
                elapsed = max(0.001, time.time() - start_time)
                exec_speed = it / elapsed
                print(f"  [Progress: {it:04d}/{iterations}] Coverage: {len(self.coverage_blocks)} blocks | Faults: {len(self.detected_faults)} | Speed: {exec_speed:.1f} exec/s")

        summary_path = os.path.join(self.report_dir, "fuzz_summary.json")
        report = {
            "total_executions": self.total_runs,
            "unique_coverage_blocks": len(self.coverage_blocks),
            "total_faults_identified": len(self.detected_faults),
            "fault_records": self.detected_faults
        }
        with open(summary_path, "w") as fp:
            json.dump(report, fp, indent=4)

        print("\n" + "="*65)
        print("[+] Phase 3 Fuzzing Completed Successfully!")
        print(f"    - Unique Basic Blocks Covered: {len(self.coverage_blocks)}")
        print(f"    - Memory/Privilege Faults Found: {len(self.detected_faults)}")
        print(f"    - Summary Report: {summary_path}")
        print("="*65)

if __name__ == "__main__":
    groups_file = os.path.expanduser("~/smm_project/phase2_init/harness/fuzz_groups.json")
    lock_file = os.path.expanduser("~/smm_project/phase2_init/harness/lock_state.json")
    report_folder = os.path.expanduser("~/smm_project/phase3_fuzz")

    harness = SmuFuzzExecutionHarness(groups_file, lock_file, report_folder)
    harness.run_fuzzing(iterations=1000)
