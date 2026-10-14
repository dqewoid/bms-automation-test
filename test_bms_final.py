import can
import cantools

# 加载DBC
db = cantools.database.load_file('battery_test.dbc')
msg_def = db.get_message_by_name('Battery_Status')

# 虚拟CAN
bus1 = can.interface.Bus(interface='virtual', channel='vcan0')  # 模拟BMS
bus2 = can.interface.Bus(interface='virtual', channel='vcan0')  # 模拟测试工具

# 测试用例（企业格式）
TEST_CASES = [
    {"case_id": "TC001", "name": "正常状态", "data": [0x64, 0x00, 0x00, 0x64, 0x00, 0x00, 0x00, 0x00],
     "expected_fault": 0},
    {"case_id": "TC002", "name": "过压故障", "data": [0x10, 0x27, 0x00, 0x64, 0x00, 0x00, 0x01, 0x00],
     "expected_fault": 1},
    {"case_id": "TC003", "name": "欠压故障", "data": [0x00, 0x00, 0x00, 0x64, 0x00, 0x00, 0x02, 0x00],
     "expected_fault": 2},
    {"case_id": "TC004", "name": "过温故障", "data": [0x64, 0x00, 0x00, 0x64, 0x00, 0x78, 0x03, 0x00],
     "expected_fault": 3},
]

print("=" * 60)
print("BMS自动化测试报告")
print("=" * 60)

results = []

for case in TEST_CASES:
    print(f"\n[执行] {case['case_id']} {case['name']}...")

    # 发送
    bus1.send(can.Message(arbitration_id=0x100, data=case['data']))

    # 接收
    recv = bus2.recv(timeout=1.0)
    if recv is None:
        print(f"  [FAIL] 无响应")
        results.append({"case_id": case['case_id'], "name": case['name'], "result": "FAIL", "reason": "无响应"})
        continue

    # DBC解析
    decoded = db.decode_message(recv.arbitration_id, recv.data)
    actual_fault = decoded['Fault_Code']

    # 判定
    if actual_fault == case['expected_fault']:
        print(f"  [PASS] Fault_Code={actual_fault}")
        results.append({"case_id": case['case_id'], "name": case['name'], "result": "PASS", "actual": actual_fault})
    else:
        print(f"  [FAIL] 期望{case['expected_fault']}, 实际{actual_fault}")
        results.append(
            {"case_id": case['case_id'], "name": case['name'], "result": "FAIL", "expected": case['expected_fault'],
             "actual": actual_fault})

# 汇总报告
print("\n" + "=" * 60)
print("测试汇总")
print("=" * 60)
print(f"{'用例ID':<10}{'名称':<15}{'结果':<10}{'详情'}")
for r in results:
    detail = f"实际Fault_Code={r.get('actual', '-')}" if r[
                                                             'result'] == 'PASS' else f"期望{r.get('expected', '-')}, 实际{r.get('actual', r.get('reason', '-'))}"
    print(f"{r['case_id']:<10}{r['name']:<15}{r['result']:<10}{detail}")

passed = sum(1 for r in results if r['result'] == 'PASS')
failed = len(results) - passed
print(f"\n总计: 通过{passed}, 失败{failed}")

bus1.shutdown()
bus2.shutdown()
