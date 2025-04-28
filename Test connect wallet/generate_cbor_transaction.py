import os
from pycardano import (
    TransactionBody, TransactionInput, TransactionId, TransactionOutput,
    Address, Network, Transaction, TransactionWitnessSet, BlockFrostChainContext,
    Value # Import thêm Value để xử lý số lượng Lovelace
)

# --- !!! THAY THẾ CÁC GIÁ TRỊ PLACEHOLDER SAU !!! ---
# Lấy Project ID từ Blockfrost.io (đăng ký miễn phí)
# Bạn có thể đặt nó làm biến môi trường hoặc thay trực tiếp vào chuỗi
blockfrost_project_id = os.environ.get("BLOCKFROST_PROJECT_ID", "YOUR_BLOCKFROST_PROJECT_ID")

# ID của giao dịch chứa UTXO bạn muốn dùng làm đầu vào
input_tx_id_hex = "YOUR_INPUT_TX_ID_HEX" # Ví dụ: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
input_tx_index = 0  # Chỉ số của UTXO trong giao dịch đó (thường là 0 hoặc 1)

# Số lượng Lovelace chính xác trong UTXO đầu vào của bạn
input_amount_lovelace = 10000000 # Ví dụ: 10 ADA = 10,000,000 Lovelace (BẠN PHẢI THAY BẰNG GIÁ TRỊ THỰC)

# Địa chỉ của bạn (để nhận tiền thừa - change)
# Sử dụng địa chỉ testnet từ ví dụ trước
my_address_bech32 = "addr_test1vrm9x2zsux7va6w892g38tvchnzahvcd9tykqf3ygnmwtaqyfg52x"

# Địa chỉ người nhận
recipient_address_bech32 = "addr_test1vr3g6va7t5k2seu4m5kwk7a6u3e4fx0j6sw3k4k5h6ry64g2l2kzp" # Ví dụ địa chỉ nhận

# Số tiền muốn gửi (ví dụ: 2 ADA)
send_amount_lovelace = 2000000

# Phí giao dịch ước tính (bạn có thể tính toán chính xác hơn bằng builder)
# Hoặc đặt một giá trị đủ lớn (ví dụ: 0.2 ADA)
fee_lovelace = 170000 # Ví dụ: 0.17 ADA
# --- !!! KẾT THÚC PHẦN THAY THẾ !!! ---

# --- Thiết lập ngữ cảnh mạng và BlockFrost ---
network = Network.TESTNET # Hoặc Network.MAINNET
context = BlockFrostChainContext(project_id=blockfrost_project_id, base_url=network.blockfrost_url)

# --- Tạo đối tượng Địa chỉ ---
try:
    my_address = Address.from_primitive(my_address_bech32)
    recipient_address = Address.from_primitive(recipient_address_bech32)
except Exception as e:
    print(f"Lỗi giải mã địa chỉ: {e}")
    exit()

# --- Tạo đối tượng Đầu vào (Input) ---
tx_id = TransactionId(bytes.fromhex(input_tx_id_hex))
tx_in = TransactionInput(transaction_id=tx_id, index=input_tx_index)

# --- Tạo đối tượng Đầu ra (Output) ---
# 1. Đầu ra cho người nhận
output_send = TransactionOutput(
    address=recipient_address,
    amount=Value(coin=send_amount_lovelace) # Sử dụng Value để chỉ định Lovelace
)

# 2. Tính toán và tạo đầu ra trả lại (Change)
change_amount_lovelace = input_amount_lovelace - send_amount_lovelace - fee_lovelace

if change_amount_lovelace < 0:
    print(f"Lỗi: Số dư đầu vào ({input_amount_lovelace}) không đủ để gửi ({send_amount_lovelace}) và trả phí ({fee_lovelace}).")
    exit()
elif change_amount_lovelace == 0:
    print("Cảnh báo: Không có tiền thừa trả lại.")
    outputs = [output_send]
else:
    output_change = TransactionOutput(
        address=my_address,
        amount=Value(coin=change_amount_lovelace)
    )
    outputs = [output_send, output_change]
    print(f"Đầu vào: {input_amount_lovelace / 1000000} ADA")
    print(f"Gửi đi: {send_amount_lovelace / 1000000} ADA")
    print(f"Phí: {fee_lovelace / 1000000} ADA")
    print(f"Trả lại: {change_amount_lovelace / 1000000} ADA")


# --- Lấy Slot hiện tại và tính TTL ---
try:
    current_slot = context.last_block_slot
    # Đặt TTL khoảng 2 giờ (7200 giây / giây mỗi slot ~ 1 => khoảng 7200 slot)
    ttl = current_slot + 7200
    print(f"Slot hiện tại: {current_slot}")
    print(f"TTL (Invalid Hereafter): {ttl}")
except Exception as e:
    print(f"Lỗi khi lấy slot hiện tại từ BlockFrost: {e}")
    print("Sử dụng TTL mặc định (có thể không hợp lệ).")
    ttl = 100000000 # Đặt một giá trị lớn tạm thời nếu không lấy được

# --- Tạo Thân Giao dịch (Transaction Body) ---
tx_body = TransactionBody(
    inputs=[tx_in],
    outputs=outputs,
    fee=fee_lovelace,
    ttl=ttl,
    network=network # Chỉ định mạng rõ ràng hơn
)

# --- Tạo Tập hợp Bằng chứng (Witness Set - rỗng vì chưa ký) ---
# Đây là cấu trúc cần thiết, chữ ký sẽ được thêm vào sau
witness_set = TransactionWitnessSet()

# --- Tạo Giao dịch Hoàn chỉnh (Kết hợp Body và Witness Set) ---
transaction = Transaction(
    transaction_body=tx_body,
    transaction_witness_set=witness_set,
    auxiliary_data=None # Không có metadata trong ví dụ này
)

# --- Tuần tự hóa Giao dịch thành CBOR Hex ---
cbor_hex = transaction.to_cbor_hex()

# --- In kết quả ---
print("\n--- Transaction Object (Python) ---")
print(transaction)

print("\n--- Raw Transaction CBOR (Hex - Chưa ký) ---")
print(cbor_hex)

print("\n--- Hướng dẫn tiếp theo ---")
print("1. Lưu CBOR hex này vào một file (ví dụ: tx.raw.cborhex).")
print("2. Sử dụng cardano-cli hoặc thư viện khác để KÝ (sign) giao dịch này bằng khóa riêng tư tương ứng với địa chỉ đầu vào.")
print("   Ví dụ cardano-cli:")
print(f"   cardano-cli transaction sign --tx-body-file <file_chứa_body_cbor> --signing-key-file <file_skey> --{network.cli_param[1:]} --out-file tx.signed")
print("   (Lưu ý: Cần trích xuất phần body CBOR từ CBOR giao dịch hoàn chỉnh ở trên nếu dùng cardano-cli)")
print("   HOẶC dùng phương thức ký của PyCardano nếu có signing key object.")
print("3. GỬI (submit) file giao dịch đã ký (tx.signed) lên mạng Cardano.")
print(f"   cardano-cli transaction submit --tx-file tx.signed --{network.cli_param[1:]}")