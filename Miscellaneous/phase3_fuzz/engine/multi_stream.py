import os
import random
import struct

class MultiStreamInput:
    """
    پیاده سازی ساختار ورودی چهار جریانی SmuFuzz
    """
    def __init__(self, handler_sel=0, comm_buf=b"", io_stream=b"", mem_stream=b""):
        self.handler_sel = handler_sel      # استریم انتخاب هندلر (UINT16)
        self.comm_buf = comm_buf            # استریم بافر داده ارتباطی (CommBuffer)
        self.io_stream = io_stream          # استریم پاسخ به خواندن از پورت‌های I/O
        self.mem_stream = mem_stream        # استریم داده‌های اشاره‌گرهای خارج از SMRAM

    @classmethod
    def generate_random(cls, comm_size=256, io_size=64, mem_size=512):
        """تولید یک نمونه ورودی چند جریانی تصادفی اولیه (Seed)"""
        return cls(
            handler_sel=random.randint(0, 0xFFFF),
            comm_buf=bytearray(random.getrandbits(8) for _ in range(comm_size)),
            io_stream=bytearray(random.getrandbits(8) for _ in range(io_size)),
            mem_stream=bytearray(random.getrandbits(8) for _ in range(mem_size))
        )

    def mutate(self):
        """جهش بایت‌ها (Mutation) به سبک LibAFL به صورت مجزا روی هر استریم"""
        # جهش روی استریم انتخاب هندلر
        if random.random() < 0.3:
            self.handler_sel = (self.handler_sel ^ random.randint(1, 0xFF)) & 0xFFFF

        # جهش روی CommBuffer (تغییر تصادفی بایت یا معکوس‌سازی بیت‌ها)
        if self.comm_buf and random.random() < 0.7:
            idx = random.randint(0, len(self.comm_buf) - 1)
            self.comm_buf[idx] = random.randint(0, 255)

        # جهش روی Mem Stream (تزریق مقادیر مرزی نظیر 0x00 یا پوینترهای مخرب)
        if self.mem_stream and random.random() < 0.5:
            idx = random.randint(0, len(self.mem_stream) - 4)
            # گاهی آدرس‌های خطرناک مانند اشاره‌گر به SMRAM یا نال تزریق می‌شود
            dangerous_tokens = [b"\x00\x00\x00\x00", b"\x00\x00\x00\x7A", b"\xFF\xFF\xFF\xFF"]
            token = random.choice(dangerous_tokens)
            self.mem_stream[idx:idx+len(token)] = token

    def serialize(self):
        """بسته‌بندی استریم‌ها در قالب یک کانتینر باینری"""
        header = struct.pack("<HIII", self.handler_sel, len(self.comm_buf), len(self.io_stream), len(self.mem_stream))
        return header + bytes(self.comm_buf) + bytes(self.io_stream) + bytes(self.mem_stream)

if __name__ == "__main__":
    test_input = MultiStreamInput.generate_random()
    print("[*] Generated Test Multi-Stream Input:")
    print(f"    - HandlerSel: {hex(test_input.handler_sel)}")
    print(f"    - CommBuffer Size: {len(test_input.comm_buf)} bytes")
    print(f"    - IO Stream Size: {len(test_input.io_stream)} bytes")
    print(f"    - Mem Stream Size: {len(test_input.mem_stream)} bytes")
    
    test_input.mutate()
    raw_data = test_input.serialize()
    print(f"[+] Successfully serialized mutated Multi-Stream payload ({len(raw_data)} bytes).")
