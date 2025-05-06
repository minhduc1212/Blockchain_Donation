# Import lớp Transaction từ thư viện (giả sử là pycardano)
from pycardano import Transaction



cbor_hex_address = "00f8977d7746faecc06b97896626f17dbfab4a71c08f0ff7da2ae449a206e7b9eff2a60015215ad82a32f879c3ec49357c4b12737f1a7caf25"
cbor_hex_string_base = "84a4008182582042263fc151905c8da840a984e9e57b05ca0323842c615585168721fa6f6700aa01018282583900f8977d7746faecc06b97896626f17dbfab4a71c08f0ff7da2ae449a206e7b9eff2a60015215ad82a32f879c3ec49357c4b12737f1a7caf251a001e848082583900415df791b636a194b1a16a1620d14ead89f75a7e6967376766f229ea317b386a943d141589fc7ac8b8e53fecb0acfd499b20125859c322d21b0000000253c9aae0021a00029810031a04baf9d5a0f5f6"
cbor_hex_string = cbor_hex_string_base.replace("00415df791b636a194b1a16a1620d14ead89f75a7e6967376766f229ea317b386a943d141589fc7ac8b8e53fecb0acfd499b20125859c322d2", cbor_hex_address)
print(f"Chuỗi hex CBOR: {cbor_hex_string}")

try:
    reconstructed_transaction = Transaction.from_cbor(cbor_hex_string)

    # --- Kết quả / Kiểm tra ---
    # Bây giờ bạn đã có lại đối tượng Transaction

    # Bạn có thể truy cập lại các thành phần của nó:
    reconstructed_tx_body = reconstructed_transaction.transaction_body
    print(f"Transaction Body: {str(reconstructed_tx_body)}")
    print(f"Outputs của Transaction Body: {str(reconstructed_tx_body.outputs[1])}")
    tx_body = str(reconstructed_tx_body.outputs[1]).splitlines()
    for line in tx_body:
        if "address" in line:
            print(f"Địa chỉ: {line.split(': ')[1].replace(',', '')}")


except ImportError:
    print("Lỗi: Không tìm thấy thư viện pycardano. Hãy đảm bảo bạn đã cài đặt nó (pip install pycardano).")
except Exception as e:
    print(f"Lỗi trong quá trình giải tuần tự hóa: {e}")
    print("Vui lòng đảm bảo chuỗi cbor_hex_string là chính xác và bạn đã cài đặt thư viện cần thiết.")