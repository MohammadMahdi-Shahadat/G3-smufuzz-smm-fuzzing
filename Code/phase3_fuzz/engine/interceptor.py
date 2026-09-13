import struct

class MemoryAndIOInterceptor:
    def __init__(self, smram_base=0x7A000000, smram_size=0x02000000):
        self.smram_base = smram_base
        self.smram_end = smram_base + smram_size
        self.redzone_base = smram_base + 0x1000  # ناحیه Redzone برای کشف خطاهای اشاره‌گر
        self.redzone_size = 0x1000
        self.read_history = {}

    def is_in_smram(self, address):
        """بررسی این‌که آیا آدرس در محدوده امن SMRAM قرار دارد یا خیر"""
        return self.smram_base <= address < self.smram_end

    def is_in_redzone(self, address):
        """بررسی نقض دسترسی به محدوده Redzone درون SMRAM"""
        return self.redzone_base <= address < (self.redzone_base + self.redzone_size)

    def handle_memory_read(self, address, size, mem_stream, fetch_count=1):
        """
        رهگیری خواندن حافظه:
        - اگر داخل SMRAM باشد: دسترسی مستقیم (یا شناسایی کرش ردزون)
        - اگر خارج از SMRAM باشد: تزریق از استریم Mem و ثبت برای کشف Double-Fetch
        """
        if self.is_in_redzone(address):
            return None, "CRASH_SMRAM_REDZONE_VIOLATION"

        if self.is_in_smram(address):
            # دسترسی معتبر درون حافظه امن
            return b"\x90" * size, "SMRAM_INTERNAL_READ"

        # دسترسی به خارج از SMRAM (هدایت پوینترها به استریم Fuzz)
        # انتخاب تکه‌ای از استریم متناسب با آدرس
        offset = (address ^ 0x5A) % max(1, len(mem_stream) - size)
        data = mem_stream[offset:offset + size]

        # بررسی شرایط وقوع باگ Double-Fetch
        if address in self.read_history:
            prev_data = self.read_history[address]
            if prev_data != data:
                return data, "VULN_DOUBLE_FETCH_DETECTED"

        self.read_history[address] = data
        return data, "NON_SMRAM_INTERCEPTED"

    def handle_memory_write(self, address, data):
        """رهگیری نوشتن حافظه: نوشتن خارج از SMRAM نادیده گرفته می‌شود"""
        if not self.is_in_smram(address):
            return "DISCARDED_NON_SMRAM_WRITE"
        return "SMRAM_INTERNAL_WRITE"

    def handle_io_read(self, port, size, io_stream):
        """پاسخ به عملیات Port I/O با مقادیر استریم IO"""
        offset = port % max(1, len(io_stream) - size)
        return io_stream[offset:offset + size]
    def reset_history(self):
        """پاکسازی تاریخچه خواندن در شروع هر چرخه اجرای SMI"""
        self.read_history.clear()

if __name__ == "__main__":
    interceptor = MemoryAndIOInterceptor()
    dummy_mem = bytearray(b"\xAA\xBB\xCC\xDD\x11\x22\x33\x44" * 10)
    dummy_io = bytearray(b"\x01\x02\x03\x04\x05\x06\x07\x08")

    print("[*] Testing Memory and I/O Interceptor:")
    
    # تست ۱: ارجاع پوینتر به خارج از SMRAM
    val, status = interceptor.handle_memory_read(0x10005000, 4, dummy_mem)
    print(f"    - Non-SMRAM Read @ 0x10005000: Status={status}, Data={val.hex()}")

    # تست ۲: تست Double-Fetch با تغییر ورودی فازر
    dummy_mem[0:4] = b"\xFF\xEE\xDD\xCC"
    val2, status2 = interceptor.handle_memory_read(0x10005000, 4, dummy_mem)
    print(f"    - Second Read (Double-Fetch Test): Status={status2}, Data={val2.hex()}")

    # تست ۳: تست دسترسی به Redzone
    _, status3 = interceptor.handle_memory_read(interceptor.redzone_base + 0x10, 4, dummy_mem)
    print(f"    - Redzone Read Access: Status={status3}")
